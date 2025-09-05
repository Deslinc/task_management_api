from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.db.session import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.models.task import Task
from app.models.user import User

get_current_user = __import__("app.dependencies.auth", fromlist=["get_current_user"]).get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = Task(
        title=payload.title,
        description=payload.description,
        status=payload.status or "todo",
        due_date=payload.due_date,
        owner_id=user.id
    )
    db.add(task); db.commit(); db.refresh(task)
    return task

@router.get("", response_model=List[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status: str | None = Query(None, description="Filter by status: todo|in_progress|done"),
    search: str | None = Query(None, description="Search in title/description"),
    due_before: datetime | None = Query(None),
    due_after: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    q = db.query(Task).filter(Task.owner_id == user.id)
    if status:
        q = q.filter(Task.status == status)
    if search:
        like = f"%{search}%"
        q = q.filter((Task.title.ilike(like)) | (Task.description.ilike(like)))
    if due_before:
        q = q.filter(Task.due_date != None).filter(Task.due_date <= due_before)
    if due_after:
        q = q.filter(Task.due_date != None).filter(Task.due_date >= due_after)

    tasks = q.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return tasks

@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if payload.title is not None: task.title = payload.title
    if payload.description is not None: task.description = payload.description
    if payload.status is not None: task.status = payload.status
    if payload.due_date is not None: task.due_date = payload.due_date
    db.commit(); db.refresh(task)
    return task

@router.patch("/{task_id}/complete", response_model=TaskOut)
def complete_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "done"
    db.commit(); db.refresh(task)
    return task

@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task); db.commit()
    return {"message": "Task deleted"}
