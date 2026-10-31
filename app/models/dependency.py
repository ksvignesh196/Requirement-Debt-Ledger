"""
Pydantic schemas for Debt Dependencies and Graph Visualizations
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DependencyCreate(BaseModel):
    debt_id: str = Field(..., description="The dependent debt item")
    depends_on_debt_id: str = Field(..., description="The debt item that blocks or is required")
    dependency_type: str = Field(default="Blocks", description="Blocks, Architectural Precondition, Data Dependency")
    notes: Optional[str] = None
    created_by: Optional[str] = "Architect"

class DependencyResponse(BaseModel):
    id: int
    debt_id: str
    depends_on_debt_id: str
    dependency_type: str
    notes: Optional[str] = None
    created_at: str

class GraphNode(BaseModel):
    id: str
    title: str
    module: str
    status: str
    risk_score: float
    risk_tier: str
    priority_index: float
    downstream_blocked_count: int

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    dependency_type: str
    notes: Optional[str] = None

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    has_cycle: bool
    cycles: List[List[str]]
    critical_path: List[str]
