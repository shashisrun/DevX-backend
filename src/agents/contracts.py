from typing import Any, Dict, List
from pydantic import BaseModel


class PlannerInput(BaseModel):
    requirements: List[str]


class PlannerOutput(BaseModel):
    dag: Dict[str, Any]
    acceptance: List[str]


class DesignerInput(BaseModel):
    plan: PlannerOutput


class DesignerOutput(BaseModel):
    openapi: Dict[str, Any]
    adrs: List[str]


class ImplementerInput(BaseModel):
    design: DesignerOutput


class ImplementerOutput(BaseModel):
    patches: List[str]


class TesterInput(BaseModel):
    patch: ImplementerOutput


class TesterOutput(BaseModel):
    report: str


class ReviewerInput(BaseModel):
    report: TesterOutput
    diff: ImplementerOutput


class ReviewerOutput(BaseModel):
    approved: bool
    comments: List[str]


class DeployerInput(BaseModel):
    build: ImplementerOutput


class DeployerOutput(BaseModel):
    image_refs: List[str]
    runbook: str


class CriticInput(BaseModel):
    artifact: str


class CriticOutput(BaseModel):
    findings: List[str]
    suggestions: List[str]
