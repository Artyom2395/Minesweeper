from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.models.config import Base

class GameDB(Base):
    __tablename__ = "games"

    game_id = Column(String, primary_key=True, index=True)
    width = Column(Integer)
    height = Column(Integer)
    mines_count = Column(Integer)
    field = Column(Text)
    completed = Column(Boolean)
    mines_positions = relationship("MinePosition", back_populates="game")

class MinePosition(Base):
    __tablename__ = "mines_positions"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, ForeignKey("games.game_id"))
    row = Column(Integer)
    col = Column(Integer)
    game = relationship("GameDB", back_populates="mines_positions")