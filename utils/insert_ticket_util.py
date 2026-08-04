from functools import lru_cache
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langsmith import traceable
from utils import get_vector_store
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def _get_resolved_ticket_summarization_chain():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an IT knowledge engineer. Extract the core technical issue "
         "and the final resolution into a dense, brief technical summary. "
         "Use the provided metadata (CI, Category) to add context if helpful."),
        ("human",
         "Short Description: {short_desc}\nFull Description: {desc}\n"
         "Category: {category}\nConfiguration Item: {cmdb_ci}\n\n"
         "Resolution Notes: {resolution}")
    ])
    return prompt | llm | StrOutputParser()

@traceable(name='ingest_tickets', run_type='chain')
def process_tickets(resolved_tickets: list):
    """
    Takes a list of validated Pydantic ticket models, summarizes them,
    and upserts them into the pgvector database.
    """
    logger.info("Starting batch ingestion", extra={"ticket_count": len(resolved_tickets)})

    summarization_chain = _get_resolved_ticket_summarization_chain()
    vector_store = get_vector_store()

    documents_to_insert = []
    document_ids = []

    for ticket in resolved_tickets:
        logger.info("Processing ticket", extra={"ticket_number": ticket.number})

        clean_summary = summarization_chain.invoke({
            "short_desc": ticket.short_description,
            "desc": ticket.description,
            "category": ticket.category,
            "cmdb_ci": ticket.cmdb_ci or "Unknown",
            "resolution": ticket.close_notes
        })

        doc = Document(
            page_content=clean_summary,
            metadata={
                "sys_id": ticket.sys_id,
                "number": ticket.number,
                "cmdb_ci": ticket.cmdb_ci,
                "category": ticket.category
            }
        )
        documents_to_insert.append(doc)
        document_ids.append(ticket.sys_id)

        logger.info("Ticket summarized", extra={"ticket_number": ticket.number})
    
    logger.info("Saving embeddings to database", extra={"document_count": len(documents_to_insert)})
    vector_store.add_documents(documents=documents_to_insert, ids=document_ids)
    logger.info("Batch ingestion complete", extra={"document_count": len(documents_to_insert)})