from pydantic import BaseModel,Field
from job_fastapi.models.candidate import JobStatus
class create_job_request(BaseModel):
    title:str=Field(min_length=3)
    description:str=Field(min_length=10)
    min_experience:int=Field(default=0,ge=-1)
    required_skills:list[str]=Field(default=[])
    nice_to_have:list[str]=Field(default=[])

class add_candidate(BaseModel):
    job_id: int
    name: str
    resume_url: str


class job_schema(BaseModel):
    id:int
    title:str
    description:str
    min_experience:int
    required_skills:list[str]
    nice_to_have:list[str]
    
class candidate_schema(BaseModel):
    id: int
    job_id: int
    name: str
    resume_url: str
    status: JobStatus