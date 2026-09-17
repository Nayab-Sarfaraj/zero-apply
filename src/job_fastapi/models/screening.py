from datetime import datetime

from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from job_fastapi.config.database import Base


class Screening(Base):
    __tablename__ = "screenings"

    id: Mapped[int] = mapped_column(primary_key=True)

    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id"),
        nullable=False
    )

    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    strengths: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list
    )

    weaknesses: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list
    )

    recommendation: Mapped[str] = mapped_column(
        String,
        nullable=True
    )

    experience_match_percentage: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    candidate: Mapped["Candidate"] = relationship(
        "Candidate",
        back_populates="screenings"
    )