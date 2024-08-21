import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
import json

from migrations.session import get_db
from migrations.models import Agent

from utils.response import response
from common.AgentPromptHandler import AgentPromptHandler
from admin.WorkspaceHelper import check_workspace_agent_manage_access

logger = logging.getLogger(__name__)

router = APIRouter()
agent_prompt_handler = AgentPromptHandler()


class AgentCreate(BaseModel):
    agent_name: str
    agent_description: Optional[str] = ''
    agent_cover: Optional[str] = '/placeholder.svg'
    creator: Optional[str] = 'admin'
    cat_id: Optional[str] = '1'
    status: int = Field(default=1, description='1-active, 0-inactive, 2-deleted')
    allow_model_choice: bool = Field(default=True)
    model: Optional[str] = None
    voice: bool = Field(default=True)
    system_prompt: dict
    files: dict = Field(default={})
    workspace_id: str


class AgentDelete(BaseModel):
    agent_id: UUID


class AgentUpdate(BaseModel):
    agent_id: UUID
    agent_name: Optional[str] = None
    agent_description: Optional[str] = None
    agent_cover: Optional[str] = None
    creator: Optional[str] = None
    cat_id: Optional[str] = None
    status: Optional[int] = None
    voice: Optional[bool] = None
    allow_model_choice: Optional[bool] = None
    model: Optional[str] = None
    system_prompt: Optional[dict] = None
    files: Optional[dict] = None
    workspace_id: str


class AgentResponse(BaseModel):
    agent_id: UUID
    agent_name: str
    agent_description: str
    agent_cover: str
    creator: str
    updated_at: datetime
    cat_id: str
    status: int
    allow_model_choice: bool
    model: Optional[str] = None
    system_prompt: dict
    files: dict
    workspace_id: str


@router.post("/add_agent")
def create_agent(
        agent_data: AgentCreate,
        request: Request,
        db: Session = Depends(get_db),
):
    """
    Create a new agent record in the database.
    """
    # check if the user has access to manage agents in the workspace
    user_jwt = request.state.user_jwt_content
    if not check_workspace_agent_manage_access(user_jwt, agent_data.workspace_id):
        return response(False, message="You do not have access to manage cases in this casebook")

    new_agent = Agent(
        agent_id=uuid4(),
        agent_name=agent_data.agent_name,
        agent_description=agent_data.agent_description,
        agent_cover=agent_data.agent_cover,
        creator=agent_data.creator,
        cat_id=agent_data.cat_id,
        status=agent_data.status,
        voice=agent_data.voice,
        allow_model_choice=agent_data.allow_model_choice,
        model=agent_data.model,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        agent_total_steps=len(agent_data.system_prompt),
        files=agent_data.files,
        workspace_id=agent_data.workspace_id
    )
    db.add(new_agent)

    # check if all item keys in the system_prompt are numbers
    if not all(k.isnumeric() for k in agent_data.system_prompt.keys()):
        return response(False, message="Prompt keys must be numeric")

    # add each item as a prompt
    for key, value in agent_data.system_prompt.items():
        # if value is dict, convert it to json
        if isinstance(value, dict):
            value = json.dumps(value)
        agent_prompt_handler.put_agent_prompt(str(new_agent.agent_id), value, key)

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
        request: Request,
        db: Session = Depends(get_db)
):
    """
    Delete an existing agent record in the database by marking it as status=2.
    Will not actually delete the record or prompt from the database.
    """
    agent_to_delete = db.query(Agent).filter(Agent.agent_id == delete_data.agent_id).first()

    # check if the user has access to manage agents in the workspace
    user_jwt = request.state.user_jwt_content
    if not check_workspace_agent_manage_access(user_jwt, agent_to_delete.workspace_id):
        return response(False, message="You do not have access to manage cases in this casebook")

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
        request: Request,
        db: Session = Depends(get_db)
):
    """
    Update an existing agent record in the database.
    """
    agent_to_update = db.query(Agent).filter(Agent.agent_id == update_data.agent_id).first()

    # check if the user has access to manage agents in the workspace that the agent from,
    # and the workspace that the agent is being moved to, if these are different
    user_jwt = request.state.user_jwt_content
    if agent_to_update.workspace_id != update_data.workspace_id:
        if not check_workspace_agent_manage_access(user_jwt, update_data.workspace_id):
            return response(False, message="You do not have access to manage cases in the casebook you are moving the case to")
    if not check_workspace_agent_manage_access(user_jwt, agent_to_update.workspace_id):
        return response(False, message="You do not have access to manage cases in this casebook")

    if not agent_to_update:
        logger.error(f"Agent not found: {update_data.agent_id}")
        response(False, status_code=404, message="Agent not found")

    # Update the agent fields if provided
    if update_data.agent_name is not None:
        agent_to_update.agent_name = update_data.agent_name
    if update_data.agent_description is not None:
        agent_to_update.agent_description = update_data.agent_description
    if update_data.agent_cover is not None:
        agent_to_update.agent_cover = update_data.agent_cover
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
    if update_data.files is not None:
        agent_to_update.files = update_data.files
    if update_data.workspace_id is not None:
        agent_to_update.workspace_id = update_data.workspace_id
    agent_to_update.updated_at = datetime.now()
    agent_to_update.agent_total_steps = len(update_data.system_prompt)

    if update_data.system_prompt is not None:
        # check if all item keys in the system_prompt are numbers
        if not all(k.isnumeric() for k in update_data.system_prompt.keys()):
            return response(False, message="Prompt keys must be numeric")

        # add each item as a prompt
        for key, value in update_data.system_prompt.items():
            # if value is dict, convert it to json
            if isinstance(value, dict):
                value = json.dumps(value)
            agent_prompt_handler.put_agent_prompt(str(agent_to_update.agent_id), value, key)

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
        request: Request,
        search: Optional[str] = None,
        workspace_id: Optional[str] = None,
        db: Session = Depends(get_db),
        page: int = 1,
        page_size: int = 10
):
    """
    List agents with pagination.
    """
    # Define the fields to be returned
    fields = (Agent.agent_name, Agent.agent_cover, Agent.agent_description, Agent.agent_id, Agent.updated_at, Agent.workspace_id)
    # Get the workspaces that the user has access to
    allowed_workspaces = list(request.state.user_jwt_content['workspace_role'].keys())

    if (search is None or search == "") and (workspace_id is None or workspace_id == ""):
        # no filter applied, get all agents that the user have access to
        query = db.query(Agent).with_entities(*fields).filter(Agent.status != 2).filter(Agent.workspace_id.in_(allowed_workspaces))

    elif (search is None or search == "") and (workspace_id is not None and workspace_id != ""):
        # no search, but filter by workspace_id

        if workspace_id not in allowed_workspaces:
            # make sure the user has access to the workspace requested
            return response(False, message="You do not have access to this casebook")

        query = db.query(Agent).with_entities(*fields).filter(Agent.status != 2).filter(Agent.workspace_id == workspace_id)

    elif (search is not None and search != "") and (workspace_id is None or workspace_id == ""):
        # search by name or description, but no filter by workspace_id
        query = (db.query(Agent).with_entities(*fields).filter(Agent.status != 2).filter(Agent.workspace_id.in_(allowed_workspaces))
                 .filter((Agent.agent_name.ilike(f"%{search}%")) | (Agent.agent_description.ilike(f"%{search}%"))))

    elif (search is not None and search != "") and (workspace_id is not None and workspace_id != ""):
        # search by name or description, and filter by workspace_id

        if workspace_id not in allowed_workspaces:
            # make sure the user has access to the workspace requested
            return response(False, message="You do not have access to this casebook")

        query = (db.query(Agent).with_entities(*fields).filter(Agent.status != 2).filter(Agent.workspace_id == workspace_id)
                 .filter((Agent.agent_name.ilike(f"%{search}%")) | (Agent.agent_description.ilike(f"%{search}%"))))

    else:
        return response(False, message="Invalid search parameters")
    total = query.count()
    query = query.order_by(Agent.updated_at.desc())
    skip = (page - 1) * page_size
    agents = query.offset(skip).limit(page_size).all()
    # Convert each tuple into a dictionary
    agents = [dict(agent_name=agent[0], agent_cover=agent[1], agent_description=agent[2], agent_id=agent[3],
                   updated_at=agent[4], workspace_id=agent[5]) for agent in agents]
    return response(True, data={"agents": agents, "total": total})


@router.get("/agent/{agent_id}")
def get_agent_by_id(
        agent_id: UUID,
        request: Request,
        db: Session = Depends(get_db)
):
    """
    Fetch an agent by its UUID.
    """
    agent = db.query(Agent).filter(Agent.agent_id == agent_id, Agent.status != 2).first()  # exclude deleted agents

    # check if the user has access to manage agents in the workspace
    user_jwt = request.state.user_jwt_content
    if not check_workspace_agent_manage_access(user_jwt, agent.workspace_id):
        return response(False, message="You do not have access to manage cases in this casebook")

    if agent is None:
        response(False, status_code=404, message="Agent not found")
    # get the prompt for the agent
    system_prompt = {}
    for step in range(0, agent.agent_total_steps):
        system_prompt[step] = agent_prompt_handler.get_agent_prompt(str(agent_id), str(step))
    agent.system_prompt = system_prompt
    if not agent.files:
        agent.files = {}
    return response(True, data=agent)
