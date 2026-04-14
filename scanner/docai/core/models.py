from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Route:
    id: str
    method: str
    path: str
    params: List[str]
    response: Optional[str]
    errors: List[int]
    dependencies: List[str]
    source_code: str