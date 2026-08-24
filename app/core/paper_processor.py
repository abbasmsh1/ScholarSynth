import os
import tempfile
import spacy
import pdfplumber
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
from datetime import datetime
import logging
import traceback
import uuid
import asyncio

from app.models.paper import Paper
from app.core.database import Base

# Setup logging
logger = logging.getLogger(__name__)

class PaperProcessor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error("Failed to load spaCy model. Please install it with: python -m spacy download en_core_web_sm")
            raise
        
        self.upload_dir = os.getenv("UPLOAD_DIR", os.path.join(tempfile.gettempdir(), "uploads"))
        os.makedirs(self.upload_dir, exist_ok=True)

    async def process_paper(self, file: Any, db: AsyncSession) -> Paper:
        """Process a PDF paper and extract relevant information"""
        temp_file_path = None
        
        try:
            # Validate file
            if not file.filename:
                raise ValueError("Missing filename")
                
            if not file.filename.lower().endswith('.pdf'):
                raise ValueError(f"Not a PDF file: {file.filename}")
            
            # Create a unique filename to avoid collisions
            unique_filename = f"{uuid.uuid4().hex}_{os.path.basename(file.filename)}"
            file_path = os.path.join(self.upload_dir, unique_filename)
            temp_file_path = file_path  # Store for cleanup in case of error
            
            logger.info(f"Saving uploaded file to {file_path}")
            
            # Save the uploaded file
            try:
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    if not content:
                        raise ValueError(f"Empty file content: {file.filename}")
                    buffer.write(content)
            except Exception as e:
                logger.error(f"Error saving file {file.filename}: {str(e)}")
                raise ValueError(f"Could not save file: {str(e)}")

            # Extract text from PDF
            text = ""
            try:
                with pdfplumber.open(file_path) as pdf:
                    if not pdf.pages:
                        raise ValueError(f"PDF has no pages: {file.filename}")
                    
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text
                
                if not text.strip():
                    raise ValueError(f"Could not extract text from PDF: {file.filename}")
            except Exception as e:
                logger.error(f"Error extracting text from {file.filename}: {str(e)}")
                raise ValueError(f"Failed to extract text from PDF: {str(e)}")

            # Process text with spaCy
            try:
                doc = self.nlp(text[:100000])  # Limit text size to avoid memory issues
            except Exception as e:
                logger.error(f"Error processing text with spaCy: {str(e)}")
                raise ValueError(f"Failed to process text with NLP: {str(e)}")

            # Extract key information
            try:
                title = self._extract_title(doc)
                authors = self._extract_authors(doc)
                abstract = self._extract_abstract(doc)
                keywords = self._extract_keywords(doc)
                references = self._extract_references(doc)
                citations = self._extract_citations(doc)
            except Exception as e:
                logger.error(f"Error extracting metadata: {str(e)}")
                raise ValueError(f"Failed to extract metadata: {str(e)}")

            # Create paper record
            try:
                paper = Paper(
                    title=title or "Untitled Paper",
                    authors=json.dumps(authors),
                    abstract=abstract,
                    keywords=json.dumps(keywords),
                    references=json.dumps(references),
                    citations=json.dumps(citations),
                    file_path=file_path,
                    processed_at=datetime.utcnow()
                )

                # Save to database
                db.add(paper)
                await db.commit()
                await db.refresh(paper)
                
                logger.info(f"Successfully processed paper: {title}")
                return paper
            except Exception as e:
                logger.error(f"Error saving paper to database: {str(e)}")
                raise ValueError(f"Failed to save paper to database: {str(e)}")

        except Exception as e:
            # If there was an error and we created a temp file, try to clean it up
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.info(f"Cleaned up temporary file after error: {temp_file_path}")
                except:
                    pass  # Ignore cleanup errors
                    
            # Log the full error
            error_traceback = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            logger.error(f"Error processing paper: {str(e)}\n{error_traceback}")
            
            # Re-raise with clear message
            if isinstance(e, ValueError):
                raise
            else:
                raise ValueError(f"Error processing paper: {str(e)}")

    async def get_all_papers(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Retrieve all papers from the database"""
        try:
            result = await db.execute(select(Paper))
            papers = result.scalars().all()
            
            # Format the papers for API response
            formatted_papers = []
            for paper in papers:
                authors_list = json.loads(paper.authors) if paper.authors else []
                keywords_list = json.loads(paper.keywords) if paper.keywords else []
                
                formatted_papers.append({
                    "id": paper.id,
                    "title": paper.title,
                    "authors": authors_list,
                    "abstract": paper.abstract,
                    "keywords": keywords_list,
                    "processed_at": paper.processed_at.isoformat() if paper.processed_at else None
                })
            
            return formatted_papers
            
        except Exception as e:
            error_traceback = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            logger.error(f"Error fetching papers: {str(e)}\n{error_traceback}")
            raise ValueError(f"Error fetching papers: {str(e)}")

    def _extract_title(self, doc) -> str:
        """Extract title from the document"""
        # Simple heuristic: first sentence is usually the title
        if doc.sents:
            return next(doc.sents).text.strip()
        return "Untitled"

    def _extract_authors(self, doc) -> List[str]:
        """Extract authors from the document"""
        # Simple heuristic: look for patterns like "Author1, Author2, and Author3"
        authors = []
        for sent in doc.sents:
            text = sent.text.lower()
            if "author" in text or "by" in text:
                # Split by common delimiters and clean up
                parts = text.split(",")
                for part in parts:
                    part = part.strip()
                    if part and not part.startswith(("author", "by")):
                        authors.append(part)
                break
        return authors if authors else ["Unknown Author"]

    def _extract_abstract(self, doc) -> str:
        """Extract abstract from the document"""
        # Look for section starting with "Abstract"
        abstract = ""
        for sent in doc.sents:
            if sent.text.lower().startswith("abstract"):
                abstract = sent.text
                break
        return abstract

    def _extract_keywords(self, doc) -> List[str]:
        """Extract keywords from the document"""
        # Look for section starting with "Keywords"
        keywords = []
        for sent in doc.sents:
            if sent.text.lower().startswith("keywords"):
                # Split by common delimiters
                parts = sent.text.split(":")[-1].split(",")
                keywords.extend([k.strip() for k in parts if k.strip()])
                break
        return keywords

    def _extract_references(self, doc) -> List[Dict[str, str]]:
        """Extract references from the document"""
        # Look for section starting with "References"
        references = []
        in_references = False
        for sent in doc.sents:
            if sent.text.lower().startswith("references"):
                in_references = True
                continue
            if in_references:
                # Basic reference parsing
                ref = {
                    "text": sent.text.strip(),
                    "authors": [],
                    "year": "",
                    "title": "",
                    "journal": ""
                }
                references.append(ref)
        return references

    def _extract_citations(self, doc) -> List[Dict[str, str]]:
        """Extract citations from the document"""
        # Look for citation patterns like [1], (Smith et al., 2020)
        citations = []
        for sent in doc.sents:
            # Look for bracketed numbers
            for token in sent:
                if token.text.startswith("[") and token.text.endswith("]"):
                    citations.append({
                        "text": token.text,
                        "reference": "",
                        "context": sent.text
                    })
            # Look for author-year citations
            text = sent.text
            if "(" in text and ")" in text:
                start = text.find("(")
                end = text.find(")")
                citation_text = text[start:end+1]
                citations.append({
                    "text": citation_text,
                    "reference": "",
                    "context": sent.text
                })
        return citations 