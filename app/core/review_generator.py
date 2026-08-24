from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from langchain.llms import Together
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
from datetime import datetime

from app.models.paper import Paper
from app.models.review import Review, Section
from app.core.database import Base

# Load environment variables
load_dotenv()

class ReviewGenerator:
    def __init__(self):
        """Initialize the review generator. The Together AI client is created
        lazily so importing/starting the app doesn't require the API key -
        only generating a review does."""
        self.together_api_key = os.getenv("TOGETHER_API_KEY")
        self._llm = None

        # Define prompts for different sections
        self.intro_prompt = PromptTemplate(
            input_variables=["topic", "papers"],
            template="""
            Write an introduction for a state-of-the-art review paper on {topic}.
            Use the following papers as references:
            {papers}
            
            The introduction should:
            1. Provide background context
            2. Explain the importance of the topic
            3. Outline the structure of the review
            """
        )
        
        self.methodology_prompt = PromptTemplate(
            input_variables=["topic", "papers"],
            template="""
            Write a methodology section for a state-of-the-art review paper on {topic}.
            Use the following papers as references:
            {papers}
            
            The methodology section should:
            1. Explain the review process
            2. Describe the paper selection criteria
            3. Outline the analysis approach
            """
        )
        
        self.results_prompt = PromptTemplate(
            input_variables=["topic", "papers"],
            template="""
            Write a results section for a state-of-the-art review paper on {topic}.
            Use the following papers as references:
            {papers}
            
            The results section should:
            1. Present key findings from the papers
            2. Compare different approaches
            3. Highlight trends and patterns
            """
        )
        
        self.discussion_prompt = PromptTemplate(
            input_variables=["topic", "papers"],
            template="""
            Write a discussion section for a state-of-the-art review paper on {topic}.
            Use the following papers as references:
            {papers}
            
            The discussion section should:
            1. Analyze the implications of findings
            2. Identify challenges and limitations
            3. Suggest future research directions
            """
        )
        
        self.conclusion_prompt = PromptTemplate(
            input_variables=["topic", "papers"],
            template="""
            Write a conclusion section for a state-of-the-art review paper on {topic}.
            Use the following papers as references:
            {papers}
            
            The conclusion should:
            1. Summarize key findings
            2. Highlight contributions
            3. Suggest future directions
            """
        )

    @property
    def llm(self) -> Together:
        if not self.together_api_key:
            raise ValueError("TOGETHER_API_KEY environment variable is not set")
        if self._llm is None:
            self._llm = Together(
                together_api_key=self.together_api_key,
                model="mistralai/Mixtral-8x7B-Instruct-v0.1"
            )
        return self._llm

    async def generate(
        self,
        paper_ids: List[str],
        topic: str,
        max_length: Optional[int] = 3000,
        db: Optional[Session] = None
    ) -> Review:
        """Generate a state-of-the-art review based on the provided papers."""
        # Fetch papers from database
        papers = db.query(Paper).filter(Paper.id.in_(paper_ids)).all()
        if not papers:
            raise ValueError("No papers found with the provided IDs")
        
        # Prepare paper information for prompts
        papers_info = "\n".join([
            f"- {paper.title} by {', '.join(author['name'] for author in paper.authors)}"
            for paper in papers
        ])
        
        # Generate sections using LLM chains
        intro_chain = LLMChain(llm=self.llm, prompt=self.intro_prompt)
        methodology_chain = LLMChain(llm=self.llm, prompt=self.methodology_prompt)
        results_chain = LLMChain(llm=self.llm, prompt=self.results_prompt)
        discussion_chain = LLMChain(llm=self.llm, prompt=self.discussion_prompt)
        conclusion_chain = LLMChain(llm=self.llm, prompt=self.conclusion_prompt)
        
        # Generate content for each section
        intro_content = await intro_chain.arun(topic=topic, papers=papers_info)
        methodology_content = await methodology_chain.arun(topic=topic, papers=papers_info)
        results_content = await results_chain.arun(topic=topic, papers=papers_info)
        discussion_content = await discussion_chain.arun(topic=topic, papers=papers_info)
        conclusion_content = await conclusion_chain.arun(topic=topic, papers=papers_info)
        
        # Create sections
        sections = [
            Section(title="Introduction", content=intro_content),
            Section(title="Methodology", content=methodology_content),
            Section(title="Results", content=results_content),
            Section(title="Discussion", content=discussion_content),
            Section(title="Conclusion", content=conclusion_content)
        ]
        
        # Generate abstract
        abstract = await self._generate_abstract(topic, papers_info)
        
        # Create database record
        db_review = Review(
            title=f"State-of-the-Art Review: {topic}",
            abstract=abstract,
            content=[section.dict() for section in sections],
            references=[paper.doi for paper in papers if paper.doi],
            topic=topic,
            paper_ids=paper_ids,
            word_count=str(sum(len(section.content.split()) for section in sections))
        )
        
        # Save to database
        db.add(db_review)
        db.commit()
        db.refresh(db_review)
        
        # Convert to Pydantic model for response
        return Review(
            id=db_review.id,
            title=db_review.title,
            abstract=db_review.abstract,
            introduction=Section(**db_review.content[0]),
            methodology=Section(**db_review.content[1]),
            results=Section(**db_review.content[2]),
            discussion=Section(**db_review.content[3]),
            conclusion=Section(**db_review.content[4]),
            references=db_review.references,
            generated_date=db_review.generated_date,
            topic=db_review.topic,
            paper_ids=db_review.paper_ids,
            citation_style="ieee",
            word_count=int(db_review.word_count)
        )
    
    async def _generate_abstract(self, topic: str, papers_info: str) -> str:
        """Generate an abstract for the review."""
        abstract_prompt = PromptTemplate(
            input_variables=["topic", "papers"],
            template="""
            Write an abstract for a state-of-the-art review paper on {topic}.
            Use the following papers as references:
            {papers}
            
            The abstract should:
            1. Provide a brief overview of the topic
            2. Explain the purpose of the review
            3. Summarize key findings
            4. Highlight implications
            """
        )
        
        abstract_chain = LLMChain(llm=self.llm, prompt=abstract_prompt)
        return await abstract_chain.arun(topic=topic, papers=papers_info)

    async def generate_review(self, paper_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Generate a state-of-the-art review for the given paper"""
        try:
            # Get paper from database
            paper = await self._get_paper(paper_id, db)
            if not paper:
                raise ValueError(f"Paper with ID {paper_id} not found")

            # Generate review sections
            sections = await self._generate_sections(paper)

            # Create review record
            review = Review(
                paper_id=paper_id,
                sections=json.dumps(sections),
                generated_at=datetime.utcnow()
            )

            # Save to database
            db.add(review)
            await db.commit()
            await db.refresh(review)

            return {
                "id": review.id,
                "paper_id": paper_id,
                "sections": sections,
                "generated_at": review.generated_at.isoformat()
            }

        except Exception as e:
            raise Exception(f"Error generating review: {str(e)}")

    async def _get_paper(self, paper_id: str, db: AsyncSession) -> Paper:
        """Get paper from database"""
        query = select(Paper).where(Paper.id == paper_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def _generate_sections(self, paper: Paper) -> List[Dict[str, Any]]:
        """Generate review sections using Together AI"""
        sections = []

        # Generate introduction
        intro = await self._generate_section(
            "introduction",
            paper.title,
            paper.abstract,
            paper.keywords
        )
        sections.append(intro)

        # Generate methodology
        methodology = await self._generate_section(
            "methodology",
            paper.title,
            paper.abstract,
            paper.keywords
        )
        sections.append(methodology)

        # Generate results
        results = await self._generate_section(
            "results",
            paper.title,
            paper.abstract,
            paper.keywords
        )
        sections.append(results)

        # Generate discussion
        discussion = await self._generate_section(
            "discussion",
            paper.title,
            paper.abstract,
            paper.keywords
        )
        sections.append(discussion)

        return sections

    async def _generate_section(
        self,
        section_type: str,
        title: str,
        abstract: str,
        keywords: str
    ) -> Dict[str, Any]:
        """Generate a specific section using Together AI"""
        # Prepare prompt based on section type
        prompt = self._create_section_prompt(
            section_type,
            title,
            abstract,
            keywords
        )

        # Call Together AI API
        response = await self._call_together_api(prompt)

        # Parse and structure the response
        return {
            "type": section_type,
            "content": response,
            "subsections": []
        }

    def _create_section_prompt(
        self,
        section_type: str,
        title: str,
        abstract: str,
        keywords: str
    ) -> str:
        """Create a prompt for the specified section"""
        prompts = {
            "introduction": f"""Write a comprehensive introduction for a research paper with the following details:
Title: {title}
Abstract: {abstract}
Keywords: {keywords}

The introduction should:
1. Provide background information
2. State the research problem
3. Present the research objectives
4. Outline the paper structure""",

            "methodology": f"""Write a detailed methodology section for a research paper with the following details:
Title: {title}
Abstract: {abstract}
Keywords: {keywords}

The methodology should:
1. Describe the research design
2. Explain the data collection process
3. Detail the analysis methods
4. Address validity and reliability""",

            "results": f"""Write a results section for a research paper with the following details:
Title: {title}
Abstract: {abstract}
Keywords: {keywords}

The results should:
1. Present the findings clearly
2. Include relevant statistics
3. Use appropriate visualizations
4. Address the research objectives""",

            "discussion": f"""Write a discussion section for a research paper with the following details:
Title: {title}
Abstract: {abstract}
Keywords: {keywords}

The discussion should:
1. Interpret the results
2. Compare with existing literature
3. Address limitations
4. Suggest future research"""
        }

        return prompts.get(section_type, "")

    async def _call_together_api(self, prompt: str) -> str:
        """Call Together AI API to generate text"""
        # TODO: Implement Together AI API call
        # For now, return a placeholder response
        return f"Generated {prompt[:50]}..." 