
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import ProcessInstance, Task, User, HistoryLog
from app.services.process_engine import ProcessEngine
from pydantic import BaseModel
from typing import List, Optional, Any

router = APIRouter()

class ProcessStartRequest(BaseModel):
    process_key: str
    user_id: int
    initial_data: dict

class TaskCompleteRequest(BaseModel):
    user_id: int
    data: dict

class TaskResponse(BaseModel):
    id: int
    name: str
    task_definition_key: str
    assignee_role: Optional[str]
    created_at: Any
    process_instance_id: int
    process_definition_key: str
    variables: dict

class HistoryResponse(BaseModel):
    action: str
    user_name: Optional[str]
    comment: Optional[str]
    timestamp: Any
    variables_snapshot: Optional[dict] = None

@router.post("/start")
def start_process(req: ProcessStartRequest, db: Session = Depends(get_db)):
    engine = ProcessEngine(db)
    instance = engine.start_process(req.process_key, req.user_id, req.initial_data)
    return {"status": "started", "id": instance.id}

@router.get("/tasks/{user_id}", response_model=List[TaskResponse])
def get_my_tasks(user_id: int, db: Session = Depends(get_db)):
    # Logic: Get tasks assigned to user OR assigned to user's Role
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    tasks = db.query(Task).join(ProcessInstance).filter(
        Task.status == "PENDING"
    ).filter(
        (Task.assignee_user_id == user_id) | (Task.assignee_role == user.role_name)
    ).all()
    
    res = []
    for t in tasks:
        res.append({
            "id": t.id,
            "name": t.name,
            "task_definition_key": t.task_definition_key,
            "assignee_role": t.assignee_role,
            "created_at": t.created_at,
            "process_instance_id": t.process_instance_id,
            "process_definition_key": t.process_instance.process_definition_key,
            "variables": t.process_instance.variables
        })
    return res

@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: int, req: TaskCompleteRequest, db: Session = Depends(get_db)):
    engine = ProcessEngine(db)
    instance = engine.complete_task(task_id, req.user_id, req.data)
    return {"status": "completed"}

@router.get("/history/{process_id}", response_model=dict)
def get_history(process_id: int, db: Session = Depends(get_db)):
    logs = db.query(HistoryLog).filter(HistoryLog.process_instance_id == process_id).order_by(HistoryLog.timestamp).all()
    instance = db.query(ProcessInstance).get(process_id)
    
    serialized_logs = []
    for log in logs:
        serialized_logs.append({
            "action": log.action,
            "user_name": log.user_name,
            "comment": log.comment,
            "timestamp": log.timestamp,
            "variables_snapshot": None # or log.variables_snapshot if added to model later
        })

    return {
        "logs": serialized_logs,
        "final_variables": instance.variables,
        "status": instance.status
    }

@router.get("/instances")
def list_instances(db: Session = Depends(get_db)):
    instances = db.query(ProcessInstance).all()
    return instances
