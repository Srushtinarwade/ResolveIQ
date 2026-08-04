from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from utils.logging_config import setup_logging
from routers import analyze, ingest

setup_logging()

app = FastAPI(title="ServiceNow LangGraph Analyzer")
app.include_router(analyze.router)
app.include_router(ingest.router)