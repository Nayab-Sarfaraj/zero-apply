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

from pydantic import BaseModel, Field


class RequirementMatch(BaseModel):
    skill: str
    matched: bool
    evidence: str | None = None


class ScreeningOutput(BaseModel):
    strengths: list[str] = Field(
        default_factory=list,
        description="The strengths of the candidate based on their resume"
    )

    weaknesses: list[str] = Field(
        default_factory=list,
        description="The weaknesses or gaps in the candidate's resume"
    )

    requirement_matches: list[RequirementMatch] = Field(
        default_factory=list,
        description="Whether the candidate matches each job requirement, with supporting evidence"
    )

    recommendation: str = Field(
        description="Overall recommendation based on the candidate's resume and job requirements"
    )
    experience_match_percentage: float
    nice_to_have_matches:list[str]=Field(description="List of skills that are in the job description nice to have section and user also have it")