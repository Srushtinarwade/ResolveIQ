from typing import Optional, TypedDict, Union

from models.ticket_models import IncidentTicket, ChangeRequestTicket

class AnalyzerState(TypedDict):
    ticket: Union[IncidentTicket, ChangeRequestTicket]
    clean_summary: str
    past_solutions: list[str]
    proposed_plan: str
    post_result: Optional[dict]