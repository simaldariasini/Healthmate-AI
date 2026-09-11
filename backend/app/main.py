from contextlib import asynccontextmanager
from datetime import date,datetime,timedelta
import base64, hashlib, hmac, json, os, secrets
from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func, select, delete
from sqlalchemy.orm import Session, joinedload
from .db import *
from .seed import seed_database
from .knowledge_service import get_relevant_knowledge,get_sources_for_entries,identify_topics
from .safety import safe_fallback,validate_ai_output
from .services import explain

@asynccontextmanager
async def lifespan(app):
 init_db(); db=SessionLocal()
 try: seed_database(db)
 finally: db.close()
 yield
app=FastAPI(title="HealthMate AI API",version="1.0.0",lifespan=lifespan)
origins=[origin.strip().rstrip("/") for origin in os.getenv("CORS_ORIGINS","http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
SECRET=os.getenv("SESSION_SECRET","development-only-change-me")
COOKIE_SECURE=os.getenv("COOKIE_SECURE","false").lower()=="true"
COOKIE_SAMESITE=os.getenv("COOKIE_SAMESITE","none" if COOKIE_SECURE else "lax")
def hash_password(p):
 salt=secrets.token_bytes(16); return base64.b64encode(salt).decode()+"$"+hashlib.pbkdf2_hmac("sha256",p.encode(),salt,210000).hex()
def verify_password(p,v):
 try:
  s,h=v.split("$"); return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256",p.encode(),base64.b64decode(s),210000).hex(),h)
 except ValueError:return False
def token(uid):
 body=base64.urlsafe_b64encode(json.dumps({"uid":uid,"exp":(datetime.utcnow()+timedelta(days=7)).timestamp()}).encode()).decode(); sig=hmac.new(SECRET.encode(),body.encode(),hashlib.sha256).hexdigest(); return body+"."+sig
def current_user(session:str|None=Cookie(None),db:Session=Depends(get_db)):
 if not session: raise HTTPException(401,"Sign in to access your personal health workspace.")
 try:
  body,sig=session.rsplit(".",1)
  if not hmac.compare_digest(sig,hmac.new(SECRET.encode(),body.encode(),hashlib.sha256).hexdigest()): raise ValueError
  data=json.loads(base64.urlsafe_b64decode(body));
  if data["exp"]<datetime.utcnow().timestamp(): raise ValueError
  user=db.get(User,data["uid"])
  if not user: raise ValueError
  return user
 except Exception: raise HTTPException(401,"Your session has expired. Please sign in again.")
class Credentials(BaseModel): email:str=Field(min_length=5,max_length=255); password:str=Field(min_length=8,max_length=128); name:str=""
class ProfileIn(BaseModel): name:str=Field(default="",max_length=120); age_range:str=""; activity_level:str=""; allergies:str=""; disliked_foods:str=""; diet:str="Vegetarian"; cuisine:str=""; cooking_time:int=Field(default=30,ge=5,le=240); condition_ids:list[int]=[]
class ReminderIn(BaseModel): title:str=Field(min_length=1,max_length=180); type:str="habit"; time:str; frequency:str="Daily"; enabled:bool=True
class AssistantIn(BaseModel): question:str=Field(min_length=2,max_length=1000); condition_ids:list[int]=[]
class PlanIn(BaseModel): week_start:date|None=None
class ReplaceIn(BaseModel): meal_id:int
class CompletionIn(BaseModel): completed:bool
class ShoppingIn(BaseModel): name:str=Field(min_length=1,max_length=180); quantity:str=""; category:str="Other"
def profile_out(u):
 p=u.profile or Profile(user_id=u.id); return {"name":u.name,"email":u.email,"age_range":p.age_range,"activity_level":p.activity_level,"allergies":p.allergies,"disliked_foods":p.disliked_foods,"diet":p.diet,"cuisine":p.cuisine,"cooking_time":p.cooking_time}
def meal_out(m):
 try: ingredients=json.loads(m.ingredients or "[]")
 except: ingredients=[]
 return {"id":m.id,"name":m.name,"description":m.description,"meal_type":m.meal_type,"cuisine":m.cuisine,"diet_type":m.diet_type,"preparation_time":m.preparation_time,"tags":m.tags,"ingredients":ingredients,"allergens":m.allergens,"instructions":m.instructions}
def compatible_meals(db:Session,u:User,slot:str|None=None,exclude_id:int|None=None):
 p=u.profile
 condition_slugs=set(db.scalars(select(HealthCondition.slug).join(UserCondition,UserCondition.condition_id==HealthCondition.id).where(UserCondition.user_id==u.id)))
 meals=list(db.scalars(select(Meal).where(Meal.is_active.is_(True))))
 def allowed(m):
  if slot and m.meal_type!=slot:return False
  if exclude_id and m.id==exclude_id:return False
  diet=(p.diet or "").lower() if p else ""
  if diet and diet not in {"non-vegetarian","no preference"} and diet not in m.diet_type.lower():return False
  allergies=[x.strip().lower() for x in (p.allergies if p else "").split(",") if x.strip()]
  if any(x in m.allergens.lower() or x in " ".join(json.loads(m.ingredients or "[]")).lower() for x in allergies):return False
  disliked=[x.strip().lower() for x in (p.disliked_foods if p else "").split(",") if x.strip()]
  if any(x in " ".join(json.loads(m.ingredients or "[]")).lower() for x in disliked):return False
  if p and p.cuisine and p.cuisine.lower() not in {"any","no preference"} and p.cuisine.lower() != m.cuisine.lower():return False
  if p and m.preparation_time > p.cooking_time:return False
  supported={x.strip() for x in m.compatible_conditions.split(",") if x.strip()}
  return not condition_slugs or condition_slugs.issubset(supported)
 return [m for m in meals if allowed(m)]
def source_out(s): return {"id":s.id,"organization":s.organization,"title":s.title,"url":s.url,"last_checked":s.last_checked}
def entry_out(e): return {"id":e.id,"claim":e.claim,"explanation":e.explanation,"topic":e.topic,"evidence_level":e.evidence_level,"population_scope":e.population_scope,"applicability":e.applicability,"limitations":e.limitations,"review_status":e.review_status,"reviewed_by":e.reviewed_by,"reviewed_at":e.reviewed_at,"next_review_at":e.next_review_at,"source":source_out(e.source),"conditions":[{"id":c.id,"name":c.name,"slug":c.slug} for c in e.conditions]}
@app.get("/api/health")
def health(): return {"status":"ok","service":"healthmate-api"}
@app.post("/api/auth/signup")
def signup(x:Credentials,response:Response,db:Session=Depends(get_db)):
 if "@" not in x.email or "." not in x.email.rsplit("@",1)[-1]: raise HTTPException(422,"Enter a valid email address.")
 if db.scalar(select(User).where(User.email==x.email.lower())): raise HTTPException(409,"An account with that email already exists.")
 u=User(email=x.email.lower(),name=x.name.strip() or x.email.split("@")[0],password_hash=hash_password(x.password)); u.profile=Profile(); db.add(u); db.commit(); db.refresh(u); response.set_cookie("session",token(u.id),httponly=True,samesite=COOKIE_SAMESITE,secure=COOKIE_SECURE,max_age=604800); return profile_out(u)
@app.post("/api/auth/login")
def login(x:Credentials,response:Response,db:Session=Depends(get_db)):
 u=db.scalar(select(User).where(User.email==x.email.lower()))
 if not u or not verify_password(x.password,u.password_hash): raise HTTPException(401,"Email or password is incorrect.")
 response.set_cookie("session",token(u.id),httponly=True,samesite=COOKIE_SAMESITE,secure=COOKIE_SECURE,max_age=604800); return profile_out(u)
@app.post("/api/auth/logout")
def logout(response:Response): response.delete_cookie("session"); return {"ok":True}
@app.get("/api/auth/me")
def me(u:User=Depends(current_user)): return profile_out(u)
@app.get("/api/conditions")
def conditions(db:Session=Depends(get_db)): return db.scalars(select(HealthCondition).where(HealthCondition.status=="active").order_by(HealthCondition.name)).all()
@app.get("/api/profile")
def get_profile(u:User=Depends(current_user),db:Session=Depends(get_db)):
 data=profile_out(u); data["condition_ids"]=list(db.scalars(select(UserCondition.condition_id).where(UserCondition.user_id==u.id))); return data
@app.put("/api/profile")
def update_profile(x:ProfileIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 p=u.profile or Profile(user_id=u.id)
 data=x.model_dump(exclude={"condition_ids","name"})
 if x.name.strip(): u.name=x.name.strip()
 for k,v in data.items(): setattr(p,k,v)
 db.add(p); db.execute(delete(UserCondition).where(UserCondition.user_id==u.id)); db.add_all([UserCondition(user_id=u.id,condition_id=i) for i in set(x.condition_ids)]); db.commit(); return get_profile(u,db)
@app.get("/api/conditions/{cid}/knowledge")
def knowledge(cid:int,topic:str="",db:Session=Depends(get_db)):
 entries=get_relevant_knowledge(db,[cid],topic); return {"entries":[entry_out(e) for e in entries],"sources":[source_out(s) for s in get_sources_for_entries(entries)]}
@app.get("/api/knowledge")
def search_knowledge(q:str="",condition_ids:str="",db:Session=Depends(get_db)):
 ids=[int(x) for x in condition_ids.split(",") if x.isdigit()] or list(db.scalars(select(HealthCondition.id))); entries=get_relevant_knowledge(db,ids,q); return {"entries":[entry_out(e) for e in entries],"topics":identify_topics(q)}
@app.get("/api/meals")
def meals(meal_type:str|None=None,u:User|None=Depends(lambda:None),db:Session=Depends(get_db)):
 q=select(Meal).where(Meal.is_active.is_(True));
 if meal_type:q=q.where(Meal.meal_type==meal_type)
 return [meal_out(m) for m in db.scalars(q.order_by(Meal.meal_type,Meal.name))]
@app.post("/api/meal-plans/generate")
def generate_plan(x:PlanIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 filtered=compatible_meals(db,u)
 if not filtered: raise HTTPException(422,"No meals safely match your saved preferences. Update your profile or ask a healthcare professional for individualized guidance.")
 plan=MealPlan(user_id=u.id,week_start=x.week_start or (date.today()-timedelta(days=date.today().weekday()))); db.add(plan); db.flush()
 slots=["breakfast","lunch","snack","dinner"]
 for day_i,day in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
  for si,slot in enumerate(slots):
   options=[m for m in filtered if m.meal_type==slot] or filtered; db.add(MealPlanItem(plan_id=plan.id,meal_id=options[(day_i+si)%len(options)].id,day=day,slot=slot))
 db.commit(); return plan_out(plan,db)
def plan_out(plan,db):
 items=db.scalars(select(MealPlanItem).options(joinedload(MealPlanItem.meal)).where(MealPlanItem.plan_id==plan.id)).all(); return {"id":plan.id,"week_start":plan.week_start,"items":[{"id":i.id,"day":i.day,"slot":i.slot,"completed":i.completed,"meal":meal_out(i.meal)} for i in items]}
@app.get("/api/meal-plans")
def plans(u:User=Depends(current_user),db:Session=Depends(get_db)): return [plan_out(p,db) for p in db.scalars(select(MealPlan).where(MealPlan.user_id==u.id).order_by(MealPlan.created_at.desc())).all()]
@app.get("/api/meal-plans/items/{item_id}/alternatives")
def alternatives(item_id:int,u:User=Depends(current_user),db:Session=Depends(get_db)):
 item=db.get(MealPlanItem,item_id); 
 if not item or db.get(MealPlan,item.plan_id).user_id!=u.id: raise HTTPException(404,"Plan item not found.")
 return [meal_out(m) for m in compatible_meals(db,u,item.slot,item.meal_id)]
@app.patch("/api/meal-plans/items/{item_id}")
def replace(item_id:int,x:ReplaceIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 item=db.get(MealPlanItem,item_id)
 if not item or db.get(MealPlan,item.plan_id).user_id!=u.id: raise HTTPException(404,"Plan item not found.")
 meal=db.get(Meal,x.meal_id)
 if not meal or meal.id not in {m.id for m in compatible_meals(db,u,item.slot)}: raise HTTPException(422,"Choose a meal compatible with your saved preferences and health topics.")
 item.meal_id=meal.id; db.commit(); return {"id":item.id,"meal":meal_out(meal)}
@app.patch("/api/meal-plans/items/{item_id}/completion")
def complete_meal(item_id:int,x:CompletionIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 item=db.get(MealPlanItem,item_id); plan=db.get(MealPlan,item.plan_id) if item else None
 if not item or not plan or plan.user_id!=u.id: raise HTTPException(404,"Plan item not found.")
 if item.completed != x.completed:
  item.completed=x.completed
  db.add(ProgressEvent(user_id=u.id,event_type="meal_completed" if x.completed else "meal_uncompleted",value=1))
  db.commit()
 return {"id":item.id,"completed":item.completed}
@app.get("/api/reminders")
def reminders(u:User=Depends(current_user),db:Session=Depends(get_db)): return db.scalars(select(Reminder).where(Reminder.user_id==u.id).order_by(Reminder.time)).all()
@app.post("/api/reminders")
def create_reminder(x:ReminderIn,u:User=Depends(current_user),db:Session=Depends(get_db)): r=Reminder(user_id=u.id,**x.model_dump()); db.add(r); db.commit(); db.refresh(r); return r
@app.patch("/api/reminders/{rid}")
def update_reminder(rid:int,x:ReminderIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 r=db.get(Reminder,rid)
 if not r or r.user_id!=u.id: raise HTTPException(404,"Reminder not found.")
 for k,v in x.model_dump().items():setattr(r,k,v)
 db.commit(); return r
@app.delete("/api/reminders/{rid}")
def delete_reminder(rid:int,u:User=Depends(current_user),db:Session=Depends(get_db)):
 r=db.get(Reminder,rid)
 if not r or r.user_id!=u.id: raise HTTPException(404,"Reminder not found.")
 db.delete(r);db.commit();return {"deleted":rid}
@app.get("/api/shopping-list")
def shopping(u:User=Depends(current_user),db:Session=Depends(get_db)): return db.scalars(select(ShoppingItem).where(ShoppingItem.user_id==u.id)).all()
@app.post("/api/shopping-list")
def add_shopping(x:ShoppingIn,u:User=Depends(current_user),db:Session=Depends(get_db)): i=ShoppingItem(user_id=u.id,**x.model_dump());db.add(i);db.commit();db.refresh(i);return i
@app.post("/api/shopping-list/regenerate/{plan_id}")
def regenerate(plan_id:int,u:User=Depends(current_user),db:Session=Depends(get_db)):
 plan=db.get(MealPlan,plan_id)
 if not plan or plan.user_id!=u.id: raise HTTPException(404,"Meal plan not found.")
 db.execute(delete(ShoppingItem).where(ShoppingItem.user_id==u.id)); totals={}
 for item in db.scalars(select(MealPlanItem).options(joinedload(MealPlanItem.meal)).where(MealPlanItem.plan_id==plan_id)):
  for raw in json.loads(item.meal.ingredients or "[]"): totals[raw.lower()]=totals.get(raw.lower(),0)+1
 for name,n in totals.items(): db.add(ShoppingItem(user_id=u.id,name=name.title(),quantity=str(n),category="Meal ingredients"))
 db.commit();return shopping(u,db)
@app.patch("/api/shopping-list/{iid}")
def toggle_shopping(iid:int,u:User=Depends(current_user),db:Session=Depends(get_db)):
 i=db.get(ShoppingItem,iid)
 if not i or i.user_id!=u.id:raise HTTPException(404,"Shopping item not found.")
 i.purchased=not i.purchased;db.commit();return i
@app.delete("/api/shopping-list/{iid}")
def delete_shopping(iid:int,u:User=Depends(current_user),db:Session=Depends(get_db)):
 i=db.get(ShoppingItem,iid)
 if not i or i.user_id!=u.id:raise HTTPException(404,"Shopping item not found.")
 db.delete(i);db.commit();return {"deleted":iid}
@app.post("/api/assistant")
def assistant(x:AssistantIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 ids=x.condition_ids or list(db.scalars(select(UserCondition.condition_id).where(UserCondition.user_id==u.id))); entries=get_relevant_knowledge(db,ids,x.question)
 if not entries:return {**safe_fallback(),"sources":[],"available_topics":[]}
 answer,model=explain(x.question,entries,u.profile); valid,violations=validate_ai_output(answer); sources=get_sources_for_entries(entries); db.add(AIAuditLog(user_id=u.id,request_summary=x.question[:300],condition_ids=json.dumps(ids),entry_ids=json.dumps([e.id for e in entries]),source_ids=json.dumps([s.id for s in sources]),model_name=model,safety_result="passed" if valid else "blocked"));db.commit()
 if not valid:return {**safe_fallback(),"sources":[],"safety_violations":violations}
 return {"message":answer,"sources":[source_out(s) for s in sources],"knowledge_entry_ids":[e.id for e in entries],"why":"HealthMate matched your question to approved, human-reviewed health information. It uses AI only to explain that context."}
@app.post("/api/assistant/preview")
def preview(x:AssistantIn,db:Session=Depends(get_db)):
 entries=get_relevant_knowledge(db,x.condition_ids,x.question)
 if not entries:return {**safe_fallback(),"sources":[]}
 return {"message":" ".join(e.explanation for e in entries[:3]),"sources":[source_out(s) for s in get_sources_for_entries(entries)]}
@app.get("/api/progress/summary")
def progress(u:User=Depends(current_user),db:Session=Depends(get_db)):
 plans=db.scalar(select(func.count(MealPlan.id)).where(MealPlan.user_id==u.id)) or 0; completed=db.scalar(select(func.count(MealPlanItem.id)).join(MealPlan).where(MealPlan.user_id==u.id,MealPlanItem.completed.is_(True))) or 0; total=db.scalar(select(func.count(MealPlanItem.id)).join(MealPlan).where(MealPlan.user_id==u.id)) or 0; reminders=db.scalar(select(func.count(Reminder.id)).where(Reminder.user_id==u.id,Reminder.enabled.is_(True))) or 0; consistency=round(completed / total * 100) if total else 0; return {"meal_plans":plans,"meals_completed":completed,"meals_planned":total,"active_reminders":reminders,"planning_consistency":consistency,"message":"Progress reflects planning and routines, not body size or appearance."}
@app.get("/")
def root():
    return {
        "message": "HealthMate AI API is running",
        "docs": "/docs"
    }