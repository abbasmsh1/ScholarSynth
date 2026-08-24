from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from sqlalchemy.ext.asyncio import AsyncSession
import traceback
import sys
import logging

from app.core.paper_processor import PaperProcessor
from app.core.review_generator import ReviewGenerator
from app.core.citation_service import CitationService
from app.models.paper import Paper
from app.models.review import Review
from app.models.citation import Citation
from app.core.database import get_db, init_db
from dotenv import load_dotenv
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

if not os.getenv("TOGETHER_API_KEY"):
    logger.warning("TOGETHER_API_KEY is not set - review generation will fail until it's configured")

app = FastAPI(
    title="AI Academic Writing Agent",
    description="An AI-powered system for generating state-of-the-art academic reviews",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
paper_processor = PaperProcessor()
review_generator = ReviewGenerator()
citation_service = CitationService()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting up application and initializing database...")
    await init_db()
    logger.info("Database initialized successfully")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that logs the error and provides a friendly response"""
    error_msg = f"Unhandled error: {str(exc)}"
    error_traceback = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error(f"{error_msg}\n{error_traceback}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

@app.get("/")
async def root():
    """Root endpoint that returns a welcome message"""
    return {
        "message": "Welcome to the AI Academic Writing Agent API",
        "version": "1.0.0",
        "endpoints": {
            "process_papers": "/api/process-papers",
            "get_papers": "/api/papers",
            "generate_review": "/api/generate-review/{paper_id}",
            "get_citations": "/api/citations/{paper_id}"
        }
    }

class ReviewRequest(BaseModel):
    papers: List[str]  # List of paper IDs or URLs
    topic: str
    max_length: Optional[int] = 3000
    citation_style: Optional[str] = "ieee"

@app.post("/api/process-papers")
async def process_papers(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Process multiple PDF papers and store them in the database.
    """
    try:
        logger.info(f"Received {len(files)} files for processing")
        
        if not files:
            logger.warning("No files were provided")
            raise HTTPException(status_code=400, detail="No files were provided")
        
        processed_papers = []
        
        for file in files:
            logger.info(f"Processing file: {file.filename}")
            if not file.filename.endswith('.pdf'):
                logger.warning(f"Skipping non-PDF file: {file.filename}")
                continue  # Skip non-PDF files
            
            try:
                paper = await paper_processor.process_paper(file, db)
                processed_papers.append({
                    "id": paper.id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "filename": file.filename
                })
                logger.info(f"Successfully processed file: {file.filename}")
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                # Continue with other files even if one fails
        
        if not processed_papers:
            logger.warning("No valid PDF files were processed")
            raise HTTPException(status_code=400, detail="No valid PDF files were provided")
            
        logger.info(f"Successfully processed {len(processed_papers)} papers")
        return {"message": f"Processed {len(processed_papers)} papers successfully", "processed_papers": processed_papers}
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_traceback = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        logger.error(f"Error in process_papers: {str(e)}\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Error processing papers: {str(e)}")

@app.get("/api/papers")
async def get_papers(db: AsyncSession = Depends(get_db)):
    """
    Get a list of all processed papers.
    """
    try:
        logger.info("Fetching all papers")
        papers = await paper_processor.get_all_papers(db)
        logger.info(f"Successfully fetched {len(papers)} papers")
        return {"papers": papers}
    except Exception as e:
        error_traceback = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        logger.error(f"Error in get_papers: {str(e)}\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Error fetching papers: {str(e)}")

@app.post("/api/generate-review/{paper_id}")
async def generate_review(
    paper_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a state-of-the-art review based on processed papers.
    """
    try:
        logger.info(f"Generating review for paper ID: {paper_id}")
        review = await review_generator.generate_review(paper_id, db)
        logger.info(f"Successfully generated review for paper ID: {paper_id}")
        return review
    except Exception as e:
        error_traceback = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        logger.error(f"Error generating review for paper ID {paper_id}: {str(e)}\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Failed to generate review: {str(e)}")

@app.get("/api/citations/{paper_id}")
async def get_citations(
    paper_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get citations from a processed paper.
    """
    try:
        logger.info(f"Fetching citations for paper ID: {paper_id}")
        citations = await citation_service.get_citations(paper_id, db)
        logger.info(f"Successfully fetched citations for paper ID: {paper_id}")
        return {"citations": citations}
    except Exception as e:
        error_traceback = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        logger.error(f"Error fetching citations for paper ID {paper_id}: {str(e)}\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch citations: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 