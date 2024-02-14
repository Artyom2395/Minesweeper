from pydantic import BaseModel
from typing import List
class Game(BaseModel):
    game_id: str
    width: int
    height: int
    mines_count: int
    field: List[List[str]]
    completed: bool

class NewGameRequest(BaseModel):
    width: int
    height: int
    mines_count: int

class TurnRequest(BaseModel):
    game_id: str
    col: int
    row: int
    
class ErrorResponse(BaseModel):
    error: str