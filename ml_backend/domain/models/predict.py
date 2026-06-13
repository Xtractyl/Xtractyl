# ml_backend/domain/models/predict.py
from __future__ import annotations

from dataclasses import dataclass

from api.contracts.predict import PredictRequest


@dataclass
class LLMConfig:
    ollama_model: str
    ollama_base: str
    system_prompt: str
    llm_timeout_seconds: int
    num_ctx: int = 4096


@dataclass
class LabelStudioConfig:
    label_studio_url: str
    ls_token: str


@dataclass
class QuestionsAndLabels:
    questions: list[str]
    labels: list[str]


@dataclass
class PredictCommand:
    job_id: str
    task_id: str
    html: str
    questions_and_labels: QuestionsAndLabels
    llm_config: LLMConfig
    label_studio_config: LabelStudioConfig

    @classmethod
    def from_contract(cls, contract: PredictRequest) -> PredictCommand:
        return cls(
            job_id=contract.job_id,
            task_id=contract.task_id,
            html=contract.html,
            questions_and_labels=QuestionsAndLabels(
                questions=contract.questions_and_labels.questions,
                labels=contract.questions_and_labels.labels,
            ),
            llm_config=LLMConfig(
                ollama_model=contract.llm_config.ollama_model,
                ollama_base=contract.llm_config.ollama_base,
                system_prompt=contract.llm_config.system_prompt,
                llm_timeout_seconds=contract.llm_config.llm_timeout_seconds,
                num_ctx=contract.llm_config.num_ctx,
            ),
            label_studio_config=LabelStudioConfig(
                label_studio_url=contract.label_studio_config.label_studio_url,
                ls_token=contract.label_studio_config.ls_token,
            ),
        )
