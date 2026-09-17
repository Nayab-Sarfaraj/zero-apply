# worker.py

import fitz
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from job_fastapi.models.job_mode import Job
from job_fastapi.models.candidate import Candidate
from job_fastapi.models.screening import Screening

from job_fastapi.config.database import DATABASE_URL

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

from job_fastapi.schema.job import ScreeningOutput
from dotenv import load_dotenv
import os
from arq.connections import RedisSettings

load_dotenv()


engine = create_engine(DATABASE_URL)

model = ChatGroq(
    model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
    max_tokens=2048,
)

structure_model = model.with_structured_output(ScreeningOutput)

prompt = PromptTemplate(
    template="""
You are an AI recruiting assistant.

Analyze the candidate's resume against the job.

Job:
Title: {title}
Description: {description}
Minimum Experience: {min_experience}
Required Skills: {required_skills}
Nice to Have: {nice_to_have}

Candidate Resume:
{resume}

Return:
- strengths
- weaknesses
- requirement_matches
- experience_match_percentage
- recommendation

Only use information present in the resume.
Do not invent experience.
""",
    input_variables=[
        "title",
        "description",
        "min_experience",
        "required_skills",
        "nice_to_have",
        "resume",
    ],
)

chain = prompt | structure_model


async def screen_candidate_job(ctx, candidate_id: int):

    with Session(engine) as db:

        candidate = db.scalar(
            select(Candidate)
            .where(Candidate.id == candidate_id)
        )

        if not candidate:
            return

        job = db.scalar(
            select(Job)
            .where(Job.id == candidate.job_id)
        )

        if not job:
            return

        # Read PDF
        docs = fitz.open(candidate.resume_url)

        text = ""

        for page in docs:
            text += page.get_text()

        docs.close()

        # LLM
        result = await chain.ainvoke({
            "title": job.title,
            "description": job.description,
            "min_experience": job.min_experience,
            "required_skills": job.required_skills,
            "nice_to_have": job.nice_to_have,
            "resume": text,
        })

        # Calculate score
        required_total = len(result.requirement_matches)

        required_matches = sum(
            1
            for requirement in result.requirement_matches
            if requirement.matched
        )

        required_score = (
            required_matches / required_total * 60
            if required_total > 0
            else 0
        )

        experience_score = (
            result.experience_match_percentage * 0.25
        )

        score = required_score + experience_score

        print("Score:", score)

        screening = Screening(
            candidate_id=candidate.id,
            score=float(score),
            strengths=result.strengths,
            weaknesses=result.weaknesses,
            recommendation=result.recommendation,
            experience_match_percentage=float(result.experience_match_percentage),
        )

        db.add(screening)
        db.commit()
        db.refresh(screening)

        print("Saved screening:", screening.id)


class WorkerSettings:
    functions=[
        screen_candidate_job
    ]
    redis_settings = RedisSettings(
        host="localhost",
        port=6379,
    )