from typing import Any, Optional
from pydantic import BaseModel
class SubmitRequest(BaseModel):
    task: str
    payload: dict

class ResponseRequest(BaseModel):
    job_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[Any] = None