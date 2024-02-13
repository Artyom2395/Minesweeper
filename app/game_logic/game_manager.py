import uuid
import random
import json
from collections import deque

from app.models.models import GameDB, MinePosition


def create_game_db(session, width, height, mines_count):
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
    
    
def reveal_cell(session, game_state, col, row):
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


def get_game_db(session, game_id):
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

def update_game_db(session, game_state):
    game = session.query(GameDB).filter(GameDB.game_id == game_state['game_id']).first()
    if game:
        game.field = json.dumps(game_state['field'])  # Сохраняем поле в виде JSON
        game.completed = game_state['completed']
        session.commit()   

def reveal_remaining_cells(session, game_state):
    width, height = game_state['width'], game_state['height']
    for row in range(height):
        for col in range(width):
            if game_state['field'][row][col] == " ":
                reveal_cell(session, game_state, col, row)
                
                
def check_game_completion(game_state):
    #width, height = game_state['width'], game_state['height']
    mines_count = game_state['mines_count']
    
    # Считаем количество не открытых ячеек
    unopened_cells_count = sum(1 for row in game_state['field'] for cell in row if cell == " ")

    # Если количество мин равно количеству не открытых ячеек, игра завершена
    return mines_count == unopened_cells_count