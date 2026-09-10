import re
from sqlalchemy import or_, select
from sqlalchemy.orm import Session,joinedload
from .db import HealthCondition,KnowledgeEntry,KnowledgeSource,ReviewStatus
TOPICS={"fiber":"fiber","fibre":"fiber","roughage":"fiber","vegetable":"vegetables","vegetables":"vegetables","veggies":"vegetables","fruit":"fruits","fruits":"fruits","protein":"protein","proteins":"protein","carb":"carbohydrates","carbohydrate":"carbohydrates","sugar":"added_sugars","sodium":"sodium","salt":"sodium","hydration":"hydration","water":"hydration","wholegrain":"whole_grains","grain":"whole_grains","grains":"whole_grains","meal":"balanced_meals","balanced":"balanced_meals","portion":"portion_awareness","label":"food_labels","legumes":"legumes","beans":"legumes","nuts":"nuts_seeds","seeds":"nuts_seeds","sleep":"sleep","activity":"physical_activity","exercise":"physical_activity","stress":"stress_management","diabetes":"diabetes","anemia":"anemia","pcos":"pcos","cholesterol":"cholesterol","hypertension":"high_blood_pressure","pressure":"high_blood_pressure"}
def identify_topics(question):
 words=re.findall(r"[a-z]+",question.lower());return list(dict.fromkeys(TOPICS[w] for w in words if w in TOPICS))
def get_relevant_knowledge(db:Session,condition_ids:list[int],question:str="",limit:int=8):
 if condition_ids:
  valid_ids=set(db.scalars(select(HealthCondition.id).where(HealthCondition.id.in_(condition_ids))))
  if not valid_ids:return []
  condition_ids=list(valid_ids)
 q=select(KnowledgeEntry).options(joinedload(KnowledgeEntry.source),joinedload(KnowledgeEntry.conditions)).outerjoin(KnowledgeEntry.conditions).where(KnowledgeEntry.review_status==ReviewStatus.approved.value)
 if condition_ids:q=q.where(or_(HealthCondition.id.in_(condition_ids),HealthCondition.id.is_(None)))
 else:q=q.where(HealthCondition.id.is_(None))
 entries=list(db.scalars(q).unique().all()); topics=identify_topics(question)
 if topics:
  matches=[e for e in entries if e.topic in topics or any(t.replace("_"," ") in (e.claim+e.explanation).lower() for t in topics)]
  if matches:entries=matches
  else:return []
 elif not condition_ids:return []
 return entries[:limit]
def get_condition_knowledge(db,condition_id):return get_relevant_knowledge(db,[condition_id])
def get_sources_for_entries(entries):return list({e.source.id:e.source for e in entries if e.source}.values())
def check_knowledge_freshness(db):return []
def validate_approval(e):return [x for x in ["source_id" if not e.source_id else None,"reviewed_by" if not e.reviewed_by else None,"reviewed_at" if not e.reviewed_at else None,"next_review_at" if not e.next_review_at else None] if x]
