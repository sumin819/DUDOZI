# llm/schemas.py

from typing import List, Literal
from pydantic import BaseModel

ActionType = Literal["supply_fertilizer", "spray"]

class TaskItem(BaseModel):
    node: str
    action: ActionType
    reason: str

class LLMResponse(BaseModel):
    task_list: List[TaskItem]
    summary_report: str