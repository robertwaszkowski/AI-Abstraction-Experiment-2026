
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, func
from sqlalchemy.orm import relationship
from .session import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    role_name = Column(String)  # 'Rector', 'Head of O.U.', etc.

class ProcessInstance(Base):
    __tablename__ = "process_instances"
    id = Column(Integer, primary_key=True, index=True)
    process_definition_key = Column(String, index=True)  # 'leave_request', etc.
    status = Column(String, default="ACTIVE") # ACTIVE, COMPLETED, REJECTED
    requester_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    variables = Column(JSON, default={})
    
    requester = relationship("User")
    tasks = relationship("Task", back_populates="process_instance")
    history_logs = relationship("HistoryLog", back_populates="process_instance")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    process_instance_id = Column(Integer, ForeignKey("process_instances.id"))
    task_definition_key = Column(String) # Task ID from BPMN
    name = Column(String) # Human readable name
    
    # Assignment
    assignee_role = Column(String, nullable=True) # Assigned to a group/role
    assignee_user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Direct assignment (optional)
    
    status = Column(String, default="PENDING") # PENDING, COMPLETED
    created_at = Column(DateTime, default=func.now())

    process_instance = relationship("ProcessInstance", back_populates="tasks")
    assignee_user = relationship("User")

class HistoryLog(Base):
    __tablename__ = "history_logs"
    id = Column(Integer, primary_key=True, index=True)
    process_instance_id = Column(Integer, ForeignKey("process_instances.id"))
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_name = Column(String, nullable=True) # Snapshot name
    action = Column(String) # START_PROCESS, COMPLETE_TASK, REJECT_APP...
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=func.now())

    process_instance = relationship("ProcessInstance", back_populates="history_logs")
    user = relationship("User")
