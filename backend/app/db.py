from datetime import date, datetime
from enum import Enum
import os
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./healthmate.db")
engine=create_engine(DATABASE_URL,connect_args={"check_same_thread":False} if DATABASE_URL.startswith("sqlite") else {})
if DATABASE_URL.startswith("sqlite"):
 @event.listens_for(engine,"connect")
 def fk(conn,_): conn.execute("PRAGMA foreign_keys=ON")
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
class Base(DeclarativeBase): pass
class ReviewStatus(str,Enum): draft="draft"; pending_review="pending_review"; approved="approved"; rejected="rejected"; archived="archived"
class User(Base):
 __tablename__="users"; id:Mapped[int]=mapped_column(primary_key=True); email:Mapped[str]=mapped_column(String(255),unique=True,index=True); password_hash:Mapped[str]=mapped_column(String(255)); name:Mapped[str]=mapped_column(String(120)); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); profile:Mapped["Profile"]=relationship(back_populates="user",uselist=False,cascade="all, delete-orphan")
class Profile(Base):
 __tablename__="profiles"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),unique=True); age_range:Mapped[str]=mapped_column(String(40),default=""); activity_level:Mapped[str]=mapped_column(String(80),default=""); allergies:Mapped[str]=mapped_column(Text,default=""); disliked_foods:Mapped[str]=mapped_column(Text,default=""); diet:Mapped[str]=mapped_column(String(80),default="Vegetarian"); cuisine:Mapped[str]=mapped_column(String(120),default=""); cooking_time:Mapped[int]=mapped_column(Integer,default=30); user:Mapped[User]=relationship(back_populates="profile")
class UserCondition(Base):
 __tablename__="user_conditions"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True); condition_id:Mapped[int]=mapped_column(ForeignKey("health_conditions.id"),index=True)
class HealthCondition(Base):
 __tablename__="health_conditions"; id:Mapped[int]=mapped_column(primary_key=True); name:Mapped[str]=mapped_column(String(120),unique=True); slug:Mapped[str]=mapped_column(String(120),unique=True,index=True); description:Mapped[str]=mapped_column(Text); status:Mapped[str]=mapped_column(String(30),default="active"); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); updated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow); entries:Mapped[list["KnowledgeEntry"]]=relationship(secondary="knowledge_condition_links",back_populates="conditions")
class KnowledgeSource(Base):
 __tablename__="knowledge_sources"; id:Mapped[int]=mapped_column(primary_key=True); organization:Mapped[str]=mapped_column(String(180)); title:Mapped[str]=mapped_column(String(240)); url:Mapped[str]=mapped_column(String(500)); source_type:Mapped[str]=mapped_column(String(80),default="official_guidance"); publication_date:Mapped[date|None]=mapped_column(Date,nullable=True); last_checked:Mapped[date]=mapped_column(Date); reliability_tier:Mapped[int]=mapped_column(Integer,default=1); description:Mapped[str]=mapped_column(Text,default=""); status:Mapped[str]=mapped_column(String(30),default="active"); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); updated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow); entries:Mapped[list["KnowledgeEntry"]]=relationship(back_populates="source")
class KnowledgeEntry(Base):
 __tablename__="knowledge_entries"; id:Mapped[int]=mapped_column(primary_key=True); source_id:Mapped[int]=mapped_column(ForeignKey("knowledge_sources.id"),index=True); claim:Mapped[str]=mapped_column(Text); explanation:Mapped[str]=mapped_column(Text); topic:Mapped[str]=mapped_column(String(100),index=True); evidence_level:Mapped[str]=mapped_column(String(100)); reliability_tier:Mapped[int]=mapped_column(Integer,default=1); population_scope:Mapped[str]=mapped_column(String(240)); applicability:Mapped[str]=mapped_column(Text); limitations:Mapped[str]=mapped_column(Text); review_status:Mapped[str]=mapped_column(String(30),default="pending_review",index=True); reviewed_by:Mapped[str|None]=mapped_column(String(120),nullable=True); reviewed_at:Mapped[date|None]=mapped_column(Date,nullable=True); next_review_at:Mapped[date|None]=mapped_column(Date,nullable=True); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); updated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow); source:Mapped[KnowledgeSource]=relationship(back_populates="entries"); conditions:Mapped[list[HealthCondition]]=relationship(secondary="knowledge_condition_links",back_populates="entries")
class KnowledgeConditionLink(Base):
 __tablename__="knowledge_condition_links"; id:Mapped[int]=mapped_column(primary_key=True); knowledge_entry_id:Mapped[int]=mapped_column(ForeignKey("knowledge_entries.id",ondelete="CASCADE")); condition_id:Mapped[int]=mapped_column(ForeignKey("health_conditions.id",ondelete="CASCADE"))
class KnowledgeReviewLog(Base):
 __tablename__="knowledge_review_log"; id:Mapped[int]=mapped_column(primary_key=True); knowledge_entry_id:Mapped[int]=mapped_column(ForeignKey("knowledge_entries.id",ondelete="CASCADE")); action:Mapped[str]=mapped_column(String(40)); previous_value:Mapped[str]=mapped_column(Text,default=""); new_value:Mapped[str]=mapped_column(Text,default=""); reviewer:Mapped[str]=mapped_column(String(120)); reason:Mapped[str]=mapped_column(Text,default=""); reviewed_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class Meal(Base):
 __tablename__="meals"; id:Mapped[int]=mapped_column(primary_key=True); name:Mapped[str]=mapped_column(String(160)); description:Mapped[str]=mapped_column(Text); meal_type:Mapped[str]=mapped_column(String(40)); cuisine:Mapped[str]=mapped_column(String(80)); diet_type:Mapped[str]=mapped_column(String(80)); preparation_time:Mapped[int]=mapped_column(Integer); tags:Mapped[str]=mapped_column(String(300)); image_url:Mapped[str]=mapped_column(String(500),default=""); is_active:Mapped[bool]=mapped_column(Boolean,default=True); ingredients:Mapped[str]=mapped_column(Text,default="[]"); allergens:Mapped[str]=mapped_column(Text,default=""); compatible_conditions:Mapped[str]=mapped_column(Text,default=""); instructions:Mapped[str]=mapped_column(Text,default="")
class MealPlan(Base):
 __tablename__="meal_plans"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True); week_start:Mapped[date]=mapped_column(Date); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class MealPlanItem(Base):
 __tablename__="meal_plan_items"; id:Mapped[int]=mapped_column(primary_key=True); plan_id:Mapped[int]=mapped_column(ForeignKey("meal_plans.id",ondelete="CASCADE")); meal_id:Mapped[int]=mapped_column(ForeignKey("meals.id")); day:Mapped[str]=mapped_column(String(12)); slot:Mapped[str]=mapped_column(String(20)); completed:Mapped[bool]=mapped_column(Boolean,default=False); meal:Mapped[Meal]=relationship()
class ShoppingItem(Base):
 __tablename__="shopping_items"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True); name:Mapped[str]=mapped_column(String(180)); quantity:Mapped[str]=mapped_column(String(80),default=""); category:Mapped[str]=mapped_column(String(80),default="Other"); purchased:Mapped[bool]=mapped_column(Boolean,default=False)
class Reminder(Base):
 __tablename__="reminders"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True); title:Mapped[str]=mapped_column(String(180)); type:Mapped[str]=mapped_column(String(40),default="habit"); time:Mapped[str]=mapped_column(String(10)); frequency:Mapped[str]=mapped_column(String(40),default="Daily"); enabled:Mapped[bool]=mapped_column(Boolean,default=True); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); updated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
class ProgressEvent(Base):
 __tablename__="progress_events"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True); event_type:Mapped[str]=mapped_column(String(60)); value:Mapped[int]=mapped_column(Integer,default=1); occurred_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class AIAuditLog(Base):
 __tablename__="ai_audit_logs"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int|None]=mapped_column(ForeignKey("users.id"),nullable=True); request_summary:Mapped[str]=mapped_column(Text); condition_ids:Mapped[str]=mapped_column(Text); entry_ids:Mapped[str]=mapped_column(Text); source_ids:Mapped[str]=mapped_column(Text); model_name:Mapped[str]=mapped_column(String(100)); safety_result:Mapped[str]=mapped_column(String(40)); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
def init_db():
 Base.metadata.create_all(bind=engine)
 # Tiny SQLite migration bridge for projects created before recipe metadata existed.
 if DATABASE_URL.startswith("sqlite"):
  from sqlalchemy import text
  with engine.begin() as conn:
   columns={r[1] for r in conn.execute(text("PRAGMA table_info(meals)"))}
   for name in ("ingredients","allergens","compatible_conditions","instructions"):
    if name not in columns: conn.execute(text(f"ALTER TABLE meals ADD COLUMN {name} TEXT DEFAULT ''"))
def get_db():
 db=SessionLocal()
 try: yield db
 finally: db.close()
