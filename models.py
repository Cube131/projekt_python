from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    """
    Model uzytkownika w systemie, przechowuje dane do logowania i saldo
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    balance = Column(Float, default=1000.0)
    is_admin = Column(Boolean, default=False)

class SpinHistory(Base):
    """
    Model historii losowan ruletki
    """
    __tablename__ = "spin_history"

    id = Column(Integer, primary_key=True, index=True)
    winning_number = Column(Integer)
    color = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())