import uuid
import random
import json
from typing import Optional
from collections import deque
from sqlalchemy.orm import Session
from app.models.models import GameDB, MinePosition


def create_game_db(session: Session, width: int, height: int, mines_count: int) -> dict:
    """
    Создает новую игру в базе данных.

    Parameters:
    - `session`: Сессия базы данных SQLAlchemy.
    - `width`: Ширина игрового поля.
    - `height`: Высота игрового поля.
    - `mines_count`: Количество мин на поле.

    Returns:
    - Словарь с информацией о новой игре.
    """
    game_id = str(uuid.uuid4())
    field = [[" " for _ in range(width)] for _ in range(height)]

    game = GameDB(
        game_id=game_id,
        width=width,
        height=height,
        mines_count=mines_count,
        field=json.dumps(field),  # Сохраняем поле в виде JSON
        completed=False,
    )
    session.add(game)

    # Генерируем расположение мин
    mines_positions = set()
    while len(mines_positions) < mines_count:
        row = random.randint(0, height - 1)
        col = random.randint(0, width - 1)
        mines_positions.add((row, col))

    # Сохраняем расположение мин в базу данных
    for row, col in mines_positions:
        mine_position = MinePosition(game_id=game_id, row=row, col=col)
        session.add(mine_position)

    session.commit()

    return {
        "game_id": game_id,
        "width": width,
        "height": height,
        "mines_count": mines_count,
        "field": field,
        "completed": False,
    }
    
    
def reveal_cell(session: Session, game_state: dict, col: int, row: int) -> None:
    """
    Раскрывает ячейку игрового поля и обновляет состояние игры.

    Parameters:
    - `session`: Сессия базы данных SQLAlchemy.
    - `game_state`: Текущее состояние игры.
    - `col`: Колонка ячейки.
    - `row`: Строка ячейки.
    """
    width, height = game_state['width'], game_state['height']
    if col < 0 or col >= width or row < 0 or row >= height or game_state['field'][row][col] != " ":
        return
    
    stack = deque([(col, row)])

    while stack:
        current_col, current_row = stack.pop()
        if game_state['field'][current_row][current_col] != " ":
            continue

        mine_count = 0
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nx, ny = current_col + dx, current_row + dy
                if 0 <= nx < width and 0 <= ny < height:
                    mine_count += session.query(MinePosition).filter_by(game_id=game_state['game_id'], row=ny, col=nx).count()

        if mine_count == 0:
            game_state['field'][current_row][current_col] = "0"
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    new_col, new_row = current_col + dx, current_row + dy
                    if 0 <= new_col < width and 0 <= new_row < height and game_state['field'][new_row][new_col] == " ":
                        stack.append((new_col, new_row))
        else:
            game_state['field'][current_row][current_col] = str(mine_count)


def get_game_db(session: Session, game_id: str) -> Optional[dict]:
    """
    Получает информацию о текущем состоянии игры из базы данных.

    Parameters:
    - `session`: Сессия базы данных SQLAlchemy.
    - `game_id`: Идентификатор игры.

    Returns:
    - Словарь с информацией о текущем состоянии игры или None, если игра не найдена.
    """
    game = session.query(GameDB).filter(GameDB.game_id == game_id).first()
    if game:
        return {
            "game_id": game.game_id,
            "width": game.width,
            "height": game.height,
            "mines_count": game.mines_count,
            "field": json.loads(game.field),  # Десериализуем поле из JSON
            "completed": game.completed,
        }
    else:
        return None

def update_game_db(session: Session, game_state: dict) -> None:
    """
    Обновляет состояние игры в базе данных.

    Parameters:
    - `session`: Сессия базы данных SQLAlchemy.
    - `game_state`: Текущее состояние игры.
    """
    game = session.query(GameDB).filter(GameDB.game_id == game_state['game_id']).first()
    if game:
        game.field = json.dumps(game_state['field'])  # Сохраняем поле в виде JSON
        game.completed = game_state['completed']
        session.commit()   

def reveal_remaining_cells(session: Session, game_state: dict) -> None:
    """
    Раскрывает все оставшиеся ячейки игрового поля.

    Parameters:
    - `session`: Сессия базы данных SQLAlchemy.
    - `game_state`: Текущее состояние игры.
    """
    width, height = game_state['width'], game_state['height']
    for row in range(height):
        for col in range(width):
            if game_state['field'][row][col] == " ":
                reveal_cell(session, game_state, col, row)
                
                
def check_game_completion(game_state: dict) -> bool:
    """
    Проверяет завершена ли игра.

    Parameters:
    - `game_state`: Текущее состояние игры.

    Returns:
    - True, если игра завершена, False в противном случае.
    """
    #width, height = game_state['width'], game_state['height']
    mines_count = game_state['mines_count']
    
    # Считаем количество не открытых ячеек
    unopened_cells_count = sum(1 for row in game_state['field'] for cell in row if cell == " ")

    # Если количество мин равно количеству не открытых ячеек, игра завершена
    return mines_count == unopened_cells_count