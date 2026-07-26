# orchestrator/db/models.py

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Float,
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
    label_studio_id = Column(Integer, nullable=True)
    is_groundtruth = Column(Boolean, nullable=False, default=False)
    ls_tasks_uploaded = Column(Boolean, nullable=False, default=False)
    questions_and_labels = Column(JSONB, nullable=True)
    labels_hash = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    project = Column(Text, ForeignKey("projects.name"), nullable=False)
    filename = Column(Text, nullable=False)
    pdf_key = Column(Text, nullable=True)
    html_key = Column(Text, nullable=True)
    pdf_hash = Column(Text, nullable=True)
    html_hash = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("project", "filename", name="uq_files_project_filename"),)


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True)
    groundtruth_project = Column(Text, ForeignKey("projects.name"), nullable=False)
    comparison_prelabelling_run_id = Column(
        Integer, ForeignKey("prelabelling_runs.id"), nullable=False
    )
    run_at = Column(TIMESTAMP(timezone=True), nullable=True)
    metrics_micro = Column(JSONB, nullable=True)
    metrics_per_label = Column(JSONB, nullable=True)
    filenames_count = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class ConversionJob(Base):
    __tablename__ = "conversion_jobs"

    id = Column(Integer, primary_key=True)
    project = Column(Text, ForeignKey("projects.name"), nullable=False)
    status = Column(Text, nullable=False, default="pending")  # pending | converting | done | failed
    total_files = Column(Integer, nullable=False)
    converted_files = Column(Integer, nullable=False, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True)
    tag = Column(Text, nullable=False)
    digest = Column(Text, nullable=False)
    archived_name = Column(Text, nullable=False, unique=True)
    size_bytes = Column(Integer, nullable=True)
    family = Column(Text, nullable=True)
    parameter_size = Column(Text, nullable=True)
    quantization_level = Column(Text, nullable=True)
    ollama_version = Column(Text, nullable=True)
    pulled_via = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="downloaded")
    first_seen_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_confirmed_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (UniqueConstraint("digest", name="uq_models_digest"),)


class PrelabellingRun(Base):
    __tablename__ = "prelabelling_runs"

    id = Column(Integer, primary_key=True)
    project = Column(Text, ForeignKey("projects.name"), nullable=False)
    label_studio_id = Column(Integer, nullable=True)
    questions_and_labels = Column(JSONB, nullable=True)
    labels_hash = Column(Text, nullable=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    system_prompt = Column(Text, nullable=True)
    llm_timeout_seconds = Column(Integer, nullable=True)
    status = Column(Text, nullable=False, default="pending")  # pending | running | done | failed
    error = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class TaskPrelabellingMeta(Base):
    __tablename__ = "task_prelabelling_metas"

    id = Column(Integer, primary_key=True)
    prelabelling_run_id = Column(Integer, ForeignKey("prelabelling_runs.id"), nullable=False)
    label_studio_task_id = Column(Integer, nullable=False)
    filename = Column(Text, nullable=False)
    predictions = Column(JSONB, nullable=True)
    raw_llm_answers = Column(JSONB, nullable=True)
    dom_match_diagnostics = Column(JSONB, nullable=True)
    dom_match_by_label = Column(JSONB, nullable=True)
    task_ms_total = Column(Float, nullable=True)
    task_ms_llm_total = Column(Float, nullable=True)
    task_ms_dom_extract = Column(Float, nullable=True)
    task_ms_dom_match = Column(Float, nullable=True)
    n_llm_calls = Column(Integer, nullable=True)
    n_timeouts = Column(Integer, nullable=True)
    avg_llm_call_ms = Column(Float, nullable=True)
    median_llm_call_ms = Column(Float, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "prelabelling_run_id",
            "label_studio_task_id",
            name="uq_task_prelabelling_meta_run_task",
        ),
    )


class TaskGroundtruthAnnotation(Base):
    __tablename__ = "task_groundtruth_annotations"

    id = Column(Integer, primary_key=True)
    project = Column(Text, ForeignKey("projects.name"), nullable=False)
    label_studio_task_id = Column(Integer, nullable=False)
    filename = Column(Text, nullable=False)
    annotations = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "project",
            "label_studio_task_id",
            name="uq_task_groundtruth_annotation_project_task",
        ),
    )
