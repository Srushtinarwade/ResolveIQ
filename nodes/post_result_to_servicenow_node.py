import os
import logging
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langsmith import traceable

from models.ticket_models import IncidentTicket
from states import AnalyzerState

logger = logging.getLogger(__name__)

_WORK_NOTE_TEMPLATE = "🤖 **AI Proposed Resolution Plan** 🤖\n\n{plan}"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    reraise=True,
)
def _post_to_snow(url, auth, headers, payload):
    return requests.patch(url, auth=auth, headers=headers, json=payload, timeout=10)


@traceable(name="servicenow_api_push", run_type="tool")
def _push_to_servicenow(
    table_name: str,
    sys_id: str,
    ticket_number: str,
    proposed_plan: str,
) -> dict:
    """
    Acts as an API client to push the AI's plan directly into the
    work_notes of the active ServiceNow ticket.
    """
    instance = os.getenv("SNOW_INSTANCE")
    user = os.getenv("SNOW_USERNAME")
    pwd = os.getenv("SNOW_PASSWORD")

    if not instance:
        logger.warning(
            "Skipping ServiceNow push: SNOW_INSTANCE not configured",
            extra={
                "ticket_number": ticket_number,
                "table": table_name,
                "sys_id": sys_id,
            },
        )
        return {
            "status": "skipped",
            "reason": "credentials_not_configured",
            "table": table_name,
            "sys_id": sys_id,
            "ticket_number": ticket_number,
        }

    url = f"https://{instance}.service-now.com/api/now/table/{table_name}/{sys_id}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {"work_notes": _WORK_NOTE_TEMPLATE.format(plan=proposed_plan)}

    try:
        response = _post_to_snow(url=url, auth=(user, pwd), headers=headers, payload=payload)

        if response.status_code in [200, 201]:
            logger.info(
                "Pushed work note to ServiceNow",
                extra={
                    "ticket_number": ticket_number,
                    "table": table_name,
                    "sys_id": sys_id,
                    "http_status": response.status_code,
                },
            )
            return {
                "status": "success",
                "http_status": response.status_code,
                "table": table_name,
                "sys_id": sys_id,
                "ticket_number": ticket_number,
            }
        else:
            logger.error(
                "Failed to push to ServiceNow",
                extra={
                    "ticket_number": ticket_number,
                    "http_status": response.status_code,
                    "response_body": response.text[:500],
                },
            )

            return {
                "status": "failed",
                "http_status": response.status_code,
                "error_body": response.text[:500],
                "table": table_name,
                "sys_id": sys_id,
                "ticket_number": ticket_number,
            }

    except requests.exceptions.RequestException as e:
        logger.error(
            "Network error pushing to ServiceNow after retries",
            extra={
                "ticket_number": ticket_number,
                "table": table_name,
                "sys_id": sys_id,
                "exception": str(e),
            },
        )
        return {
            "status": "error",
            "exception": str(e),
            "table": table_name,
            "sys_id": sys_id,
            "ticket_number": ticket_number,
        }


def post_result_to_servicenow_node(state: AnalyzerState) -> dict:
    """
    LangGraph node: Reads the proposed plan from state and pushes it
    back to the originating ServiceNow ticket as a work note.
    """
    ticket = state["ticket"]
    proposed_plan = state["proposed_plan"]

    table_name = "incident" if isinstance(ticket, IncidentTicket) else "change_request"

    result = _push_to_servicenow(
        table_name=table_name,
        sys_id=ticket.sys_id,
        ticket_number=ticket.number,
        proposed_plan=proposed_plan,
    )

    return {"post_result": result}