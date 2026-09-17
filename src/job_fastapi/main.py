from fastapi import FastAPI,status,Depends,HTTPException,UploadFile,File,Form
from job_fastapi.config.database import Base,get_db,engine
from job_fastapi.schema.job import create_job_request,job_schema,add_candidate,ScreeningOutput
from job_fastapi.models.job_mode import Job
from job_fastapi.models.candidate import Candidate
from sqlalchemy.orm import Session
from sqlalchemy  import select
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from contextlib import asynccontextmanager
from arq import create_pool
from arq.connections import RedisSettings
import os
import fitz

load_dotenv()
app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await create_pool(
        RedisSettings(
            host="localhost",
            port=6379
        )
    )

    yield

    await app.state.redis.close()


app = FastAPI(lifespan=lifespan)


Base.metadata.create_all(bind=engine)

MODEL_NAME = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

model = ChatGroq(
    model=MODEL_NAME,
    max_tokens=2048,
)

structure_model=model.with_structured_output(ScreeningOutput)

prompt = PromptTemplate(
    template="""
These are the job details:

Title: {title}
Description: {description}
Minimum Experience: {min_experience}
Required Skills: {required_skills}
Nice to Have: {nice_to_have}

Candidate Resume:
{resume}
""",
    input_variables=[
        "title",
        "description",
        "min_experience",
        "required_skills",
        "nice_to_have",
        "resume"
    ]
)

@app.post("/jobs",response_model=job_schema,status_code=status.HTTP_201_CREATED)
def create_job(job_request:create_job_request,db:Session=Depends(get_db)):
    job = Job(**job_request.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@app.get("/jobs",response_model=list[job_schema],status_code=status.HTTP_200_OK)
def get_all_job(db:Session=Depends(get_db)):
    jobs=db.scalars(select(Job)).all()
    return jobs

@app.get("/jobs/{job_id}",response_model=job_schema,status_code=status.HTTP_200_OK)
def get_job_by_id(job_id:int,db:Session=Depends(get_db)):
    job=db.scalar(select(Job).where(Job.id==job_id))
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Job with id {job_id} does not exist")

    return job

@app.post(
    "/jobs/{job_id}/candidates",
    status_code=status.HTTP_201_CREATED
)
async def add_candidate(
    job_id: int,
    name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    job = db.scalar(
        select(Job).where(Job.id == job_id)
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with {job_id} is not found"
        )

    contents = await file.read()

    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(contents)

    resume_url = f"uploads/{file.filename}"

    new_candidate = Candidate(
        job_id=job_id,
        name=name,
        resume_url=resume_url
    )

    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)

    return new_candidate

@app.get("/candidates/{candidate_id}",status_code=status.HTTP_200_OK)
def get_candidate(candidate_id:int,db:Session=Depends(get_db)):
    candiate=db.scalar(select(Candidate).where(Candidate.id == candidate_id))
    if not candiate :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Candidate with id {candidate_id} is not found")
    return candiate

@app.get("/jobs/{job_id}/candidates")
def get_candidates(job_id:int,db:Session=Depends(get_db)):
    candidates =  db.scalars(select(Candidate).where(Candidate.job_id ==job_id)).all()
    if len(candidates)==0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"None applied to this")
    return candidates

@app.post("/upload")
async def upload_file(file:UploadFile=File(...)):
    print(file.filename)
    print(file.content_type)

    contents = await file.read()
    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(contents)

    return {
        "filename": file.filename,
        "content_type": file.content_type
    }


@app.post("/candidates/{candidate_id}/screen")
async def screen_candidate(
    candidate_id: int,
    db: Session = Depends(get_db)
):

    candidate = db.scalar(
        select(Candidate)
        .where(Candidate.id == candidate_id)
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate does not exist"
        )

    job = await app.state.redis.enqueue_job(
        "screen_candidate_job",
        candidate_id
    )

    return {
        "message": "Screening started",
        "job_id": job.job_id,
        "status": "queued"
    }

@app.get("/uploads")
def get_file_content():
    docs=fitz.open("uploads/nayab_appristine.pdf")
    text=""
    for page in docs:
        print(page.get_text())
        text+=page.get_text()
    docs.close()
    return {"text":text}

@app.get("/")
def index():
    return {"status":status.HTTP_200_OK,"message":"Server is running 💀....."}































