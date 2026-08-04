import logging
from typing import Union

from fastapi import APIRouter, BackgroundTasks, Depends

from dependencies import verify_webhook_secret
from graph.workflow import workflow
from models.ticket_models import ChangeRequestTicket, IncidentTicket

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(verify_webhook_secret)])


def _ticket_type(ticket: Union[IncidentTicket, ChangeRequestTicket]) -> str:
    return "incident" if isinstance(ticket, IncidentTicket) else "change_request"


def run_analyzer_graph(ticket: Union[IncidentTicket, ChangeRequestTicket]) -> None:
    ticket_type = _ticket_type(ticket)
    logger.info(
        "Starting LangGraph analysis",
        extra={"ticket_number": ticket.number, "sys_id": ticket.sys_id, "ticket_type": ticket_type},
    )

    initial_state = {"ticket": ticket, "clean_summary": "", "past_solutions": [], "proposed_plan": ""}
    config = {
        "configurable": {"thread_id": ticket.sys_id},
        "metadata": {
            "ticket_number": ticket.number,
            "sys_id": ticket.sys_id,
            "priority": ticket.priority.value,
            "cmdb_ci": ticket.cmdb_ci,
            "category": getattr(ticket, "category", None),
            "ticket_type": ticket_type,
        },
        "tags": ["v1", ticket_type],
        "run_name": f"resolve_{ticket.number}",
    }
    workflow.invoke(initial_state, config=config)

    logger.info(
        "LangGraph analysis complete",
        extra={"ticket_number": ticket.number, "sys_id": ticket.sys_id, "ticket_type": ticket_type},
    )


@router.post("/incident/new", status_code=202)
async def process_new_incident(incident: IncidentTicket, background_tasks: BackgroundTasks):
    """Accepts a new incident from ServiceNow and triggers AI analysis."""
    logger.info("New incident received", extra={"ticket_number": incident.number})
    background_tasks.add_task(run_analyzer_graph, incident)
    return {"status": "success", "message": f"New incident {incident.number} received"}


@router.post("/change/new", status_code=202)
async def process_new_change(change: ChangeRequestTicket, background_tasks: BackgroundTasks):
    """Accepts a new change request from ServiceNow and triggers AI analysis."""
    logger.info("New change request received", extra={"ticket_number": change.number})
    background_tasks.add_task(run_analyzer_graph, change)
    return {"status": "success", "message": f"New change {change.number} received"}
