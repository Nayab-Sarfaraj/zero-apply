from datetime import datetime

from sqlalchemy.orm import mapped_column,Mapped
from job_fastapi.config.database import Base
from sqlalchemy import String, Enum as SQLEnum,ForeignKey
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from enum import Enum

class JobStatus(str, Enum):
    APPLIED="applied"
    SHORTLISTED="shortlisted"
    INTERVIEWING="interviewing"
    REJECTED="rejected"
    HIRED="hired"

class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String,nullable=False)
    job_id:Mapped[int]=mapped_column(ForeignKey("jobs.id"),nullable=False)
    resume_url:Mapped[str]=mapped_column(String,nullable=False)
    status: Mapped[JobStatus] = mapped_column(
    SQLEnum(JobStatus),
    default=JobStatus.APPLIED,
    nullable=False
)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, nullable=False
    )
    job:Mapped["Job"]=relationship(back_populates="candidates")
    screenings: Mapped[list["Screening"]] = relationship(
        "Screening",
        back_populates="candidate"
    )