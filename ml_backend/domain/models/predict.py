# ml_backend/domain/models/predict.py
from __future__ import annotations

from dataclasses import dataclass

from api.contracts.predict import PredictRequest


@dataclass
class LLMConfig:
    ollama_model: str
    system_prompt: str


@dataclass
class LabelStudioConfig:
    ls_token: str


@dataclass
class QuestionsAndLabels:
    questions: list[str]
    labels: list[str]


@dataclass
class PredictCommand:
    job_id: str
    task_id: str
    filename: str
    html: str
    questions_and_labels: QuestionsAndLabels
    llm_config: LLMConfig
    label_studio_config: LabelStudioConfig

    @classmethod
    def from_contract(cls, contract: PredictRequest) -> PredictCommand:
        return cls(
            job_id=contract.job_id,
            task_id=contract.task_id,
            filename=contract.filename,
            html=contract.html,
            questions_and_labels=QuestionsAndLabels(
                questions=contract.questions_and_labels.questions,
                labels=contract.questions_and_labels.labels,
            ),
            llm_config=LLMConfig(
                ollama_model=contract.llm_config.ollama_model,
                system_prompt=contract.llm_config.system_prompt,
            ),
            label_studio_config=LabelStudioConfig(
                ls_token=contract.label_studio_config.ls_token,
            ),
        )
