from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class DocumentFacts(BaseModel):
    title: str = "行政通知"
    target: Optional[str] = None
    deadline: Optional[str] = None
    actions: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    submission_method: Optional[str] = None
    contact: Optional[str] = None
    fee: Optional[str] = None
    cautions: list[str] = Field(default_factory=list)
    evidence_notes: list[str] = Field(default_factory=list)


class ResidentView(BaseModel):
    summary: str
    deadline: Optional[str] = None
    actions: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    contact: Optional[str] = None


class StaffView(BaseModel):
    improvement_points: list[str] = Field(default_factory=list)
    ambiguous_expressions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    document: DocumentFacts
    resident: ResidentView
    staff: StaffView
    warnings: list[str] = Field(default_factory=list)
    mode: str = "sample"
