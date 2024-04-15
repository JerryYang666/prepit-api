from sqlalchemy.sql import text
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from migrations.models import Agent
from utils.response import response
import logging

from migrations.session import get_db

router = APIRouter()


# class AgentRequest(BaseModel):
#     agent_id: UUID
#     user_id: UUID | None = None #I was thinking in the future we may want to track this??


@router.get("/get/{agent_id}")
def get_agent_by_id(
        agent_id: str,
        db: Session = Depends(get_db)
):
    """
    This function gets the settings of an agent by its ID
    :param agent_id: The ID of the agent
    :param db: The database session
    :return: The settings of the agent
    """
    if not check_uuid_format(agent_id):
        return response(False, status_code=400, message="Invalid UUID format")
    agent = db.query(Agent).filter(Agent.agent_id == agent_id, Agent.status != 2).first()  # exclude deleted agents
    if agent is None:
        response(False, status_code=404, message="Agent not found")

    logging.info(f"User requested agent settings: {agent}")

    if agent is None:
        return response(False, status_code=404, message="Agent not found")
    elif agent.status != 1:
        return response(False, status_code=404, message="Agent is inactive")
    else:
        return response(True, data={
            "agent_name": agent.agent_name,
        })


def check_uuid_format(agent_id):
    """
    This function checks if the UUID is in the correct format
    :param agent_id: The UUID to check
    :return: True if the UUID is in the correct format, False otherwise
    """
    try:
        UUID(agent_id)
    except ValueError:
        return False
    return True
