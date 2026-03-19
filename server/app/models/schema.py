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
    function_name: str
    method: str
    path: str
    parameters: List[Parameter]
    status_codes: List[StatusCode]
    source_code: str


class AnalyzeRequest(BaseModel):
    scanner_version: str
    repository: str
    commit: str
    framework: str
    routes: List[Route]