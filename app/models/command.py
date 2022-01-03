from typing import List
from pydantic import BaseModel

class Command(BaseModel):
    commands: List[str] = []