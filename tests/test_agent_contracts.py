import pytest
from pydantic import BaseModel
from typing import Type

from src.agents import (
    PlannerInput,
    PlannerOutput,
    DesignerInput,
    DesignerOutput,
    ImplementerInput,
    ImplementerOutput,
    TesterInput,
    TesterOutput,
    ReviewerInput,
    ReviewerOutput,
    DeployerInput,
    DeployerOutput,
    CriticInput,
    CriticOutput,
    agent_registry,
)


@pytest.mark.parametrize(
    "model,data",
    [
        (PlannerInput, {"requirements": ["feature"]}),
        (
            PlannerOutput,
            {"dag": {"nodes": [], "edges": []}, "acceptance": ["done"]},
        ),
        (DesignerInput, {"plan": PlannerOutput(dag={}, acceptance=[])}),
        (DesignerOutput, {"openapi": {}, "adrs": []}),
        (ImplementerInput, {"design": DesignerOutput(openapi={}, adrs=[])}),
        (ImplementerOutput, {"patches": []}),
        (TesterInput, {"patch": ImplementerOutput(patches=[])}),
        (TesterOutput, {"report": "ok"}),
        (
            ReviewerInput,
            {
                "report": TesterOutput(report="ok"),
                "diff": ImplementerOutput(patches=[]),
            },
        ),
        (ReviewerOutput, {"approved": True, "comments": []}),
        (DeployerInput, {"build": ImplementerOutput(patches=[])}),
        (DeployerOutput, {"image_refs": [], "runbook": ""}),
        (CriticInput, {"artifact": ""}),
        (CriticOutput, {"findings": [], "suggestions": []}),
    ],
)
def test_serialization_round_trip(model: Type[BaseModel], data: dict):
    obj = model(**data)
    dumped = obj.model_dump_json()
    loaded = model.model_validate_json(dumped)
    assert obj == loaded


def test_registry_roles():
    roles = [
        "planner",
        "designer",
        "implementer",
        "tester",
        "reviewer",
        "deployer",
        "critic",
    ]
    for role in roles:
        assert role in agent_registry
        assert callable(agent_registry[role])
