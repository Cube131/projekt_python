"""
Endpointy HTTP API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db, SessionLocal
from models import User, SpinHistory
from schemas import UserAuth, TokenResponse, UserResponse, FundOperation
from security import get_password_hash, verify_password, create_access_token, verify_token

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_current_user(
    authorization: Optional[str] = Header(None), 
    db: Session = Depends(get_db)
) -> User:
    """Weryfikuje token JWT i zwraca użytkownika"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Brak tokenu autoryzacyjnego")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Nieprawidłowy token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Nieprawidłowy token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Użytkownik nie istnieje")
    
    return user


# Strony HTML

@router.get("/")
def read_root(request: Request):
    """Strona główna gry"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/admin")
def read_admin(request: Request):
    """Panel administratora"""
    return templates.TemplateResponse("admin.html", {"request": request})


# Logowanie / rejestracja

@router.post("/register", response_model=TokenResponse)
def register(user_data: UserAuth, db: Session = Depends(get_db)):
    """Rejestracja nowego użytkownika"""
    try:
        db_user = db.query(User).filter(User.username == user_data.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Uzytkownik istnieje")
        
        hashed_pwd = get_password_hash(user_data.password)
        new_user = User(username=user_data.username, password=hashed_pwd)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        access_token = create_access_token(
            data={"user_id": new_user.id, "username": new_user.username}
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": new_user
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(user_data: UserAuth, db: Session = Depends(get_db)):
    """Logowanie użytkownika"""
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=401, detail="Bledne dane")
    
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/api/me", response_model=UserResponse)
def get_current_user_data(current_user: User = Depends(get_current_user)):
    """Pobiera dane zalogowanego użytkownika"""
    return current_user


# Endpointy admina

@router.get("/api/users", response_model=List[UserResponse])
def get_all_users(current_user: User = Depends(get_current_user)):
    """Pobiera wszystkich użytkowników"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Brak uprawnień")
    
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return users
    finally:
        db.close()


@router.post("/api/admin/funds")
def manage_funds(op: FundOperation, current_user: User = Depends(get_current_user)):
    """Zarządzanie środkami: dodaj, usuń, ustaw"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Brak uprawnień")
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == op.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if op.operation == 'add':
            user.balance += op.amount
        elif op.operation == 'remove':
            user.balance -= op.amount
            if user.balance < 0:
                user.balance = 0.0
        elif op.operation == 'set':
            user.balance = op.amount
        else:
            raise HTTPException(status_code=400, detail="Unknown operation")

        db.commit()
        return {
            "message": "Success",
            "new_balance": user.balance,
            "username": user.username
        }
    finally:
        db.close()


@router.get("/api/admin/history")
def get_spin_history(limit: int = 100, current_user: User = Depends(get_current_user)):
    """Pobiera historię losowań z bazy danych"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Brak uprawnień")
    
    db = SessionLocal()
    try:
        history = db.query(SpinHistory).order_by(
            SpinHistory.id.desc()
        ).limit(limit).all()
        
        # Statystyki
        total = db.query(SpinHistory).count()
        color_stats = db.query(
            SpinHistory.color,
            func.count(SpinHistory.id).label('count')
        ).group_by(SpinHistory.color).all()
        
        return {
            "total_spins": total,
            "statistics": {c: count for c, count in color_stats},
            "history": [
                {
                    "id": h.id,
                    "number": h.winning_number,
                    "color": h.color,
                    "timestamp": h.timestamp.strftime("%Y-%m-%d %H:%M:%S") if h.timestamp else "N/A"
                }
                for h in history
            ]
        }
    finally:
        db.close()
