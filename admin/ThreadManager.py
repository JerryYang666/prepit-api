# Copyright (c) 2024.
# -*-coding:utf-8 -*-
"""
@file: ThreadManager.py
@author: Jerry(Ruihuang)Yang
@email: rxy216@case.edu
@time: 6/19/24 16:50
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID, uuid4

from utils.response import response
from common.MessageStorageHandler import MessageStorageHandler
from common.FeedbackStorageHandler import FeedbackStorageHandler

from migrations.session import get_db

from sqlalchemy.orm import Session

from migrations.models import Thread, Agent

from common.DynamicAuth import DynamicAuth

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize the MessageStorageHandler
message_handler = MessageStorageHandler()
feedback_handler = FeedbackStorageHandler()


class ThreadListQuery(BaseModel):
    user_id: Optional[str] = None
    start_date: Optional[
        str] = None
    end_date: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    agent_id: Optional[str] = None


class ThreadContent(BaseModel):
    thread_id: str
    user_id: str
    created_at: str
    agent_id: str


@router.get("/new_thread")
def get_new_thread(agent_id: str, request: Request, db: Session = Depends(get_db)):
    user_jwt = request.state.user_jwt_content
    user_id = user_jwt['user_id']
    student_id = user_jwt['student_id']
    user_name = user_jwt['first_name'] + " " + user_jwt['last_name']
    user_workspaces = user_jwt['workspace_role']
    try:
        agent_query = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        agent_name = agent_query.agent_name
        workspace_id = agent_query.workspace_id
        if user_workspaces.get(workspace_id, None) is None:
            return response(False, status_code=401, message="You are unauthorized to use this case")
    except Exception as e:
        logger.error(f"Error fetching agent info: {e}")
        return response(False, status_code=500, message="Please try again later")
    thread_id = str(uuid4())
    created_at = datetime.now()
    try:
        thread = Thread(thread_id=thread_id,
                        user_id=user_id,
                        created_at=created_at,
                        agent_id=agent_id,
                        agent_name=agent_name,
                        workspace_id=workspace_id,
                        last_trial_timestamp=created_at,
                        student_id=student_id,
                        user_name=user_name)
        db.add(thread)
        db.commit()
        return response(True, data={"thread_id": thread_id})
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating new thread: {e}")
        return response(False, status_code=500, message="Please try again later")


@router.get("/get_thread/{thread_id}")
def get_thread_by_id(thread_id: UUID):
    """
    Fetch all entries for a specific thread by its UUID, sorted by creation time.
    """
    try:
        thread_messages = message_handler.get_thread(str(thread_id))
        thread_feedback = feedback_handler.get_feedback_for_thread(str(thread_id))
        if not thread_messages:
            return response(False, status_code=404, message="Interview not found")

        # Sort the messages by 'created_at' time in ascending order
        sorted_messages = sorted(thread_messages, key=lambda x: x.created_at)
        # Sort the feedback by 'step_id' in ascending order
        sorted_feedback = sorted(thread_feedback, key=lambda x: x.step_id)
        return response(True, data={"thread_id": thread_id,
                                    "messages": sorted_messages,
                                    "feedback": sorted_feedback})
    except Exception as e:
        logger.error(f"Error fetching thread content: {e}")
        response(False, status_code=500, message=str(e))


@router.get("/get_thread_list")
def get_thread_list(
        request: Request,
        db: Session = Depends(get_db),
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        workspace_id: Optional[str] = None,
        admin_mode: Optional[bool] = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
):
    """
    List threads with pagination, filtered by agent creator.
   """
    query = None
    if admin_mode:
        if not workspace_id:
            return response(False, status_code=400, message="Workspace ID is required in admin mode")
        # check user is teacher of workspace or system admin
        user_workspaces = request.state.user_jwt_content['workspace_role']
        if user_workspaces.get(workspace_id, None) != "teacher" and not request.state.user_jwt_content['system_admin']:
            return response(False, status_code=401,
                            message="You are unauthorized. Attempting to access workspace you are not a teacher of.")
        query = db.query(Thread).filter(Thread.workspace_id == workspace_id)
    else:
        user_id = request.state.user_jwt_content['user_id']
        query = db.query(Thread).filter(Thread.user_id == user_id)
        if workspace_id:
            query = query.filter(Thread.workspace_id == workspace_id)

    if search:
        query = query.filter((Thread.agent_name.ilike(f"%{search}%")) | (Thread.student_id.ilike(f"%{search}%")) | (
            Thread.user_name.ilike(f"%{search}%")))

    # if start_date:
    #     try:
    #         start_datetime = datetime.fromisoformat(start_date)
    #         query = query.filter(Thread.created_at >= start_datetime)
    #     except ValueError:
    #         raise response(False, status_code=400,
    #                        message="Invalid start_date format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")
    # if end_date:
    #     try:
    #         end_datetime = datetime.fromisoformat(end_date)
    #         query = query.filter(Thread.created_at <= end_datetime)
    #     except ValueError:
    #         raise response(False, status_code=400,
    #                        message="Invalid end_date format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")
    total = query.count()
    threads = (query.order_by(Thread.last_trial_timestamp.desc()).
               offset((page - 1) * page_size).
               limit(page_size).all())
    results = [{"thread_id": str(t.thread_id),
                "user_id": t.user_id,
                "created_at": str(t.created_at),
                "agent_id": str(t.agent_id),
                "agent_name": str(t.agent_name),
                "workspace_id": str(t.workspace_id),
                "last_trial_timestamp": str(t.last_trial_timestamp),
                "status": "Finished" if t.finished else "In Progress",
                "student_id": t.student_id,
                "user_name": t.user_name
                } for t in threads]
    return response(True, data={"threads": results, "total": total})


class ValidateThreadID(BaseModel):
    thread_id: str
    dynamic_auth_code: str


@router.post("/validate_id")
def validate_thread_id(validate: ValidateThreadID, db: Session = Depends(get_db)):
    """
    Validate the thread ID by looking up the thread in the SQL database.
    """
    dynamic_auth = DynamicAuth()
    if not dynamic_auth.verify_auth_code(validate.dynamic_auth_code):
        return response(False, status_code=401, message="Invalid auth code")
    try:
        thread = db.query(Thread).filter(Thread.thread_id == validate.thread_id).first()
        if thread is None:
            return response(False, status_code=404, message="Thread not found")
        elif thread.finished:
            return response(False, status_code=400, message="Thread is already finished")
        thread.last_trial_timestamp = datetime.now()
        db.commit()
        return response(True, data={"agent_id": str(thread.agent_id), "user_id": str(thread.user_id)})
    except Exception as e:
        logger.error(f"Error validating thread ID: {e}")
        return response(False, status_code=401, message="Please try again later")


@router.get("/finish_thread")
def finish_thread(thread_id: str, auth_code: str, db: Session = Depends(get_db)):
    """
    Mark the thread as finished.
    """
    # check if the thread id is a valid UUID
    dynamic_auth = DynamicAuth()
    if not dynamic_auth.verify_auth_code(auth_code):
        return response(False, status_code=401, message="Invalid auth code")
    try:
        UUID(thread_id)
    except ValueError:
        return response(False, status_code=400, message="Invalid thread ID")
    try:
        thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()
        if thread is None:
            return response(False, status_code=404, message="Thread not found")
        thread.finished = True
        db.commit()
        return response(True)
    except Exception as e:
        logger.error(f"Error finishing thread: {e}")
        db.rollback()
        return response(False, status_code=500, message="Please try again later")
