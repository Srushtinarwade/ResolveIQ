import logging
from langchain_core.output_parsers import StrOutputParser
from states import AnalyzerState
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


# we do not want to build the summarizer chain everytime we are calling summarize_ticket_node
#
_summarizer_chain = ChatPromptTemplate.from_messages([
    ("system",
        "Extract the core technical issue from the ServiceNow ticket data. "
        "Ignore noise. Output a dense brief technical summary."),
    ("human", "Short Description: {short_desc}\n\nFull Description: {full_desc}")
]) | ChatGoogleGenerativeAI(model="gemini-2.5-flash") | StrOutputParser()

def summarize_ticket_node(state: AnalyzerState) -> dict:
    ticket = state["ticket"]
    logger.info(
        "Summarizing ticket",
        extra={"ticket_number": ticket.number, "sys_id": ticket.sys_id},
    )
    full_desc = ticket.description or ""
    clean_summary = _summarizer_chain.invoke({
        "short_desc": ticket.short_description,
        "full_desc": full_desc
    })
    logger.info(
        "Ticket summarized",
        extra={"ticket_number": ticket.number, "summary_length": len(clean_summary)},
    )
    return {"clean_summary": clean_summary}