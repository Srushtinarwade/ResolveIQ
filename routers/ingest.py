import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends

from dependencies import verify_webhook_secret
from models.ticket_models import ResolvedTicket
from utils import process_tickets

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(verify_webhook_secret)])


@router.post("/incident/resolved", status_code=202)
async def process_resolved_incident(ticket: ResolvedTicket, background_tasks: BackgroundTasks):
    """Accepts a newly resolved incident and adds it to the knowledge base."""
    logger.info("Ingesting resolved incident", extra={"ticket_number": ticket.number, "source": "real_time"})
    background_tasks.add_task(process_tickets, [ticket])
    return {"status": "success", "message": f"Learning from incident {ticket.number}"}


@router.post("/change/resolved", status_code=202)
async def process_resolved_change(ticket: ResolvedTicket, background_tasks: BackgroundTasks):
    """Accepts a newly resolved change request and adds it to the knowledge base."""
    logger.info("Ingesting resolved change request", extra={"ticket_number": ticket.number, "source": "real_time"})
    background_tasks.add_task(process_tickets, [ticket])
    return {"status": "success", "message": f"Learning from change {ticket.number}"}


@router.post("/ingest/batch", status_code=202)
async def process_batch_ingestion(tickets: List[ResolvedTicket], background_tasks: BackgroundTasks):
    """Accepts a batch of resolved tickets from ServiceNow for background ingestion."""
    logger.info("Batch ingestion request received", extra={"ticket_count": len(tickets)})
    background_tasks.add_task(process_tickets, tickets)
    return {"status": "success", "message": f"Batch of {len(tickets)} tickets accepted"}
