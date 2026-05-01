from pydantic import BaseModel
from typing import List, Optional,Union


class Parameter(BaseModel):
    name: str
    type: str
    required: bool
    default: Optional[Union[str, int, float, bool]]


class StatusCode(BaseModel):
    code: int
    detail: str


class Route(BaseModel):
    # 🔥 support both names
    function_name: Optional[str] = None
    function: Optional[str] = None

    method: str
    path: str

    # 🔥 support both
    parameters: Optional[List[Parameter]] = []
    params: Optional[List[dict]] = []

    status_codes: Optional[List[StatusCode]] = []
    errors: Optional[List[dict]] = []

    source_code: Optional[str] = ""

    # 🔥 allow extra fields (IMPORTANT)
    calls: Optional[List[str]] = []
    call_graph: Optional[dict] = {}
    impact: Optional[List[str]] = []
    response: Optional[dict] = {}
    db_ops: Optional[List[dict]] = []
    breaking_changes: Optional[List[dict]] = {}


class AnalyzeRequest(BaseModel):
    scanner_version: str
    repository: str
    commit: str

    # 🔥 FIX HERE
    framework: Optional[str] = None
    frameworks: Optional[List[str]] = []

    routes: List[Route]
    metadata: Optional[dict] = {}