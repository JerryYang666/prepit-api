from sqlalchemy.sql import text
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
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
    conn = db.connection()
    result = conn.execute(text("select * from ai_agents where agent_id = '" + str(agent_id) + "'"))
    row = result.first()
    logging.info(f"User requested agent settings: {row}")

    if row is None:
        return response(False, status_code=404, message="Agent not found")
    elif row[7] != 1:  # the row[7] -= 1 checks if the model is not active
        return response(False, status_code=404, message="Agent is inactive")
    else:
        return response(True, data={
            "agent_name": row[2],
            "course_id": row[3],
            "voice": row[6],
            "model_choice": row[8],
            "model": row[9],
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
