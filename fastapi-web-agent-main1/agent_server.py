# ==============================================================================
# File: agent_server.py
# ==============================================================================

# Step 1: Load environment variables from the .env file.
# This MUST be the first thing to happen so that all other modules can access the keys.
from dotenv import load_dotenv
load_dotenv()

# Step 2: Import standard Python libraries
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

# Step 3: Import third-party libraries
import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# Step 4: Import from your own project files
from schemas.api_models import AnalysisRequest, AnalysisResponse, ChatRequest, ChatResponse, CompanyInfo
from utils.security import get_api_key
from processing.web_scraper import scrape_homepage_content
from processing.ai_analyzer import analyze_content_with_llm, answer_follow_up_question


# Asynchronous context manager for the application's lifespan (e.g., startup/shutdown events)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the application.
    Connects to Redis on startup for rate limiting.
    """
    print("Application startup...")
    try:
        # Get Redis URL from environment variables, with a default for local development
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_connection = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_connection)
        print("Successfully connected to Redis for rate limiting.")
    except Exception as e:
        print(f"CRITICAL: Could not connect to Redis. Rate limiting will NOT work. Error: {e}")
    
    yield  # The application is now running
    
    print("Application shutdown.")


# Initialize the FastAPI application
app = FastAPI(
    title="Advanced FastAPI AI Agent for Website Intelligence",
    description="An API for extracting and interpreting business insights from websites.",
    version="1.0.0",
    lifespan=lifespan
)

# Add Cross-Origin Resource Sharing (CORS) middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# A general exception handler to catch any unhandled errors and return a 500 status
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"An unhandled error occurred: {exc}")
    return HTTPException(status_code=500, detail=f"An internal server error occurred: {exc}")


# --- API Endpoints ---

@app.get("/", summary="Health Check", tags=["Status"])
async def read_root():
    """A simple health check endpoint to verify the service is running."""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "version": "1.0.0",
        "service": "AI Business Insights Agent"
    }

@app.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analyze a Website Homepage",
    dependencies=[Depends(get_api_key), Depends(RateLimiter(times=5, minutes=1))],
    tags=["Analysis"]
)
async def analyze_website(request: AnalysisRequest):
    """
    Scrapes a website's homepage, analyzes its content using an LLM,
    and returns structured business insights.
    
    - **url**: The target website URL.
    - **questions**: Optional list of specific questions to answer.
    """
    try:
        scraped_data = await scrape_homepage_content(str(request.url))
        if not scraped_data.get('main_content') or not scraped_data['main_content'].strip():
            raise HTTPException(
                status_code=404,
                detail="Could not find any meaningful text content on the homepage."
            )
        
        analysis_result = await analyze_content_with_llm(scraped_data, request.questions)
        
        response = AnalysisResponse(
            url=str(request.url),
            analysis_timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            company_info=CompanyInfo(**analysis_result.get("company_info", {})),
            extracted_answers=analysis_result.get("extracted_answers", [])
        )
        return response
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error during /analyze for {request.url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"An unexpected error occurred while analyzing the website: {str(e)}"
        )

@app.post(
    "/chat",
    response_model=ChatResponse,
    summary="Conversational Follow-up",
    dependencies=[Depends(get_api_key), Depends(RateLimiter(times=15, minutes=1))],
    tags=["Analysis"]
)
async def conversational_chat(request: ChatRequest):
    """
    Enables conversational follow-up questions about a website.
    
    - **url**: The website URL to discuss.
    - **query**: The user's question.
    - **conversation_history**: Optional context from previous turns.
    """
    try:
        scraped_data = await scrape_homepage_content(str(request.url))
        if not scraped_data.get('main_content') or not scraped_data['main_content'].strip():
            raise HTTPException(
                status_code=404,
                detail="Could not find any meaningful text content on the homepage."
            )
        
        agent_response, context_sources = await answer_follow_up_question(
            scraped_data=scraped_data,
            query=request.query,
            history=request.conversation_history
        )
        
        response = ChatResponse(
            url=str(request.url),
            user_query=request.query,
            agent_response=agent_response,
            context_sources=context_sources
        )
        return response
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error during /chat for {request.url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"An unexpected error occurred while processing the chat request: {str(e)}"
        )