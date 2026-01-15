"""
Modele Pydantic dla walidacji danych API
"""
from pydantic import BaseModel


class UserAuth(BaseModel):
    """Dane do logowania/rejestracji"""
    username: str
    password: str


class UserResponse(BaseModel):
    """Dane użytkownika w odpowiedzi API"""
    id: int
    username: str
    balance: float
    is_admin: bool


class TokenResponse(BaseModel):
    """Odpowiedź zawierająca token JWT"""
    access_token: str
    token_type: str
    user: UserResponse


class FundOperation(BaseModel):
    """Operacja zarządzania środkami użytkownika"""
    user_id: int
    amount: float
    operation: str  # 'add', 'remove', 'set'
