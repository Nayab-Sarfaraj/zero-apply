from datetime import datetime

from sqlalchemy.orm import mapped_column,Mapped
from job_fastapi.config.database import Base

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    min_experience: Mapped[int] = mapped_column(default=0)

    required_skills: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list
    )
    nice_to_have: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, nullable=False
    )
    candidates: Mapped[list["Candidate"]] = relationship(
        back_populates="job"
    )