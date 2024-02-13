from fastapi import Depends, FastAPI, HTTPException

from sqlalchemy.orm import Session
from app.models.config import SessionLocal, engine
from app.models.models import Base, GameDB, MinePosition
from app.api.shemas.shemas import Game, NewGameRequest, TurnRequest
from app.game_logic.game_manager import create_game_db, reveal_cell, get_game_db, update_game_db, reveal_remaining_cells, check_game_completion
from main import app

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/new", response_model=Game)
def create_new_game(request: NewGameRequest, session: Session = Depends(get_db)):
    game_state = create_game_db(session, request.width, request.height, request.mines_count)
    return Game(**game_state)

@app.post("/api/turn", response_model=Game)
def make_turn(request: TurnRequest, session: Session = Depends(get_db)):
    game_state = get_game_db(session, request.game_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game_state['field'][request.row][request.col] != " ":
        raise HTTPException(status_code=400, detail="error")
    
    mines_positions = session.query(MinePosition).filter(MinePosition.game_id == game_state['game_id']).all()
    hit_mine = (request.row, request.col) in [(mine.row, mine.col) for mine in mines_positions]

    if hit_mine:
        game_state['completed'] = True
        game_state['field'] = [['X' if (row, col) in [(mine.row, mine.col) for mine in mines_positions] else ' ' for col in range(game_state['width'])] for row in range(game_state['height'])]
        reveal_remaining_cells(session, game_state)
        update_game_db(session, game_state)
        return Game(**game_state)
    else:
        reveal_cell(session, game_state, request.col, request.row)
        game_state['completed'] = check_game_completion(game_state)

    update_game_db(session, game_state)

    if game_state['completed']:
        for mine in mines_positions:
            game_state['field'][mine.row][mine.col] = 'M'
        update_game_db(session, game_state)

    return Game(**game_state)