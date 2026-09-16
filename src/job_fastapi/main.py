from fastapi import FastAPI,status,Depends,HTTPException
from job_fastapi.config.database import Base,get_db,engine
from job_fastapi.schema.job import create_job_request,job_schema,add_candidate
from job_fastapi.models.job_mode import Job
from job_fastapi.models.candidate import Candidate
from sqlalchemy.orm import Session
from sqlalchemy  import select

app = FastAPI()

Base.metadata.create_all(bind=engine)

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

@app.post("/jobs/{job_id}/candidates",status_code=status.HTTP_201_CREATED)
def add_candidate(candidate:add_candidate,db:Session=Depends(get_db)):
    job=db.scalar(select(Job).where(Job.id == candidate.job_id))
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Job with {candidate.job_id} is not found")
    new_candidate = Candidate(**candidate.model_dump())
    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)
    return new_candidate

@app.get("/jobs/{job_id}/candidates",status_code=status.HTTP_200_OK)
def get_candidates(job_id:int,db:Session=Depends(get_db)):
    candidates = db.scalars(select(Candidate).where(Candidate.job_id==job_id)).all()
    return candidates

@app.get("/candidates/{candidate_id}",status_code=status.HTTP_200_OK)
def get_candidate(candidate_id:int,db:Session=Depends(get_db)):
    candiate=db.scalar(select(Candidate).where(Candidate.id == candidate_id))
    if not candiate :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Candidate with id {candidate_id} is not found")
    return candiate


@app.get("/")
def index():
    return {"status":status.HTTP_200_OK,"message":"Server is running 💀....."}































