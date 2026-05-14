# orchestrator/db/models.py

from sqlalchemy import (
    TIMESTAMP,
    Column,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    questions_and_labels = Column(JSONB, nullable=False)
    label_studio_id = Column(Integer, nullable=True)
    ollama_model = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    llm_timeout_seconds = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    project = Column(Text, ForeignKey("projects.name"), nullable=False)
    filename = Column(Text, nullable=False)
    pdf_path = Column(Text, nullable=True)
    html_path = Column(Text, nullable=True)
    pdf_key = Column(Text, nullable=True)
    html_key = Column(Text, nullable=True)
    pdf_hash = Column(Text, nullable=True)
    html_hash = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("project", "filename", name="uq_files_project_filename"),)


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True)
    project = Column(Text, ForeignKey("projects.name"), nullable=False)
    groundtruth_project = Column(Text, nullable=False)
    comparison_project = Column(Text, nullable=False)
    model = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    run_at = Column(TIMESTAMP(timezone=True), nullable=True)
    metrics_micro = Column(JSONB, nullable=True)
    metrics_per_label = Column(JSONB, nullable=True)
    performance = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
