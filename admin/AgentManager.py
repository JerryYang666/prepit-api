import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from migrations.session import get_db
from migrations.models import Agent

from utils.response import response
from common.AgentPromptHandler import AgentPromptHandler

logger = logging.getLogger(__name__)

router = APIRouter()
agent_prompt_handler = AgentPromptHandler()


class AgentCreate(BaseModel):
    agent_name: str
    course_id: Optional[str] = None
    creator: Optional[str] = None
    voice: bool = Field(default=False)
    status: int = Field(default=1, description='1-active, 0-inactive, 2-deleted')
    allow_model_choice: bool = Field(default=True)
    model: Optional[str] = None
    system_prompt: str


class AgentDelete(BaseModel):
    agent_id: UUID


class AgentUpdate(BaseModel):
    agent_id: UUID
    agent_name: Optional[str] = None
    course_id: Optional[str] = None
    creator: Optional[str] = None
    voice: Optional[bool] = None
    status: Optional[int] = None
    allow_model_choice: Optional[bool] = None
    model: Optional[str] = None
    system_prompt: str


class AgentResponse(BaseModel):
    agent_id: UUID
    agent_name: str
    course_id: Optional[str] = None
    creator: Optional[str] = None
    voice: bool
    status: int
    allow_model_choice: bool
    model: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    system_prompt: str


@router.post("/add_agent")
def create_agent(
        agent_data: AgentCreate,
        db: Session = Depends(get_db)
):
    """
    Create a new agent record in the database.
    """
    new_agent = Agent(
        agent_id=uuid4(),
        created_at=datetime.now(),
        agent_name=agent_data.agent_name,
        course_id=agent_data.course_id,
        creator=agent_data.creator,
        updated_at=datetime.now(),
        voice=agent_data.voice,
        status=agent_data.status,
        allow_model_choice=agent_data.allow_model_choice,
        model=agent_data.model
    )
    db.add(new_agent)
    agent_prompt_handler.put_agent_prompt(str(new_agent.agent_id), agent_data.system_prompt, '0')

    try:
        db.commit()
        db.refresh(new_agent)
        logger.info(f"Inserted new agent: {new_agent.agent_id} - {new_agent.agent_name}")
        return response(True, {"agent_id": str(new_agent.agent_id)})
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to insert new agent: {e}")
        response(False, message=str(e))


@router.post("/delete_agent")
def delete_agent(
        delete_data: AgentDelete,
        db: Session = Depends(get_db)
):
    """
    Delete an existing agent record in the database by marking it as status=2.
    Will not actually delete the record or prompt from the database.
    """
    agent_to_delete = db.query(Agent).filter(Agent.agent_id == delete_data.agent_id).first()
    if not agent_to_delete:
        logger.error(f"Agent not found: {delete_data.agent_id}")
        response(False, status_code=404, message="Agent not found")
    try:
        # mark the agent as deleted by setting the status to 2
        agent_to_delete.status = 2
        db.commit()
        logger.info(f"Deleted agent: {delete_data.agent_id}")
        return response(True, {"agent_id": str(delete_data.agent_id)})
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete agent: {e}")
        response(False, message=str(e))


@router.post("/update_agent")
def edit_agent(
        update_data: AgentUpdate,
        db: Session = Depends(get_db)
):
    """
    Update an existing agent record in the database.
    """
    agent_to_update = db.query(Agent).filter(Agent.agent_id == update_data.agent_id).first()
    if not agent_to_update:
        logger.error(f"Agent not found: {update_data.agent_id}")
        response(False, status_code=404, message="Agent not found")

    # Update the agent fields if provided
    if update_data.agent_name is not None:
        agent_to_update.agent_name = update_data.agent_name
    if update_data.course_id is not None:
        agent_to_update.course_id = update_data.course_id
    if update_data.creator is not None:
        agent_to_update.creator = update_data.creator
    if update_data.voice is not None:
        agent_to_update.voice = update_data.voice
    if update_data.status is not None:
        agent_to_update.status = update_data.status
    if update_data.allow_model_choice is not None:
        agent_to_update.allow_model_choice = update_data.allow_model_choice
    if update_data.model is not None:
        agent_to_update.model = update_data.model
    agent_to_update.updated_at = datetime.now()

    if update_data.system_prompt is not None:
        agent_prompt_handler.put_agent_prompt(str(agent_to_update.agent_id), update_data.system_prompt, '0')

    try:
        db.commit()
        db.refresh(agent_to_update)
        logger.info(f"Updated agent: {agent_to_update.agent_id}")
        return response(True, {"agent_id": str(agent_to_update.agent_id)})
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update agent: {e}")
        response(False, message=str(e))


@router.get("/agents")
def list_agents(
        creator: str,
        db: Session = Depends(get_db),
        page: int = 1,
        page_size: int = 10
):
    """
    List agents with pagination.
    """
    query = db.query(Agent).filter(Agent.creator == creator, Agent.status != 2)  # exclude deleted agents
    total = query.count()
    query = query.order_by(Agent.updated_at.desc())
    skip = (page - 1) * page_size
    agents = query.offset(skip).limit(page_size).all()
    # get the prompt for each agent
    for agent in agents:
        agent.system_prompt = agent_prompt_handler.get_agent_prompt(str(agent.agent_id), '0') or ""
    return response(True, data={"agents": agents, "total": total})


@router.get("/agent/{agent_id}")
def get_agent_by_id(
        agent_id: UUID,
        db: Session = Depends(get_db)
):
    """
    Fetch an agent by its UUID.
    """
    agent = db.query(Agent).filter(Agent.agent_id == agent_id, Agent.status != 2).first()  # exclude deleted agents
    if agent is None:
        response(False, status_code=404, message="Agent not found")
    return response(True, data=agent)
