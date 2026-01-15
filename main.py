import asyncio
import json
from datetime import datetime
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from database import engine, Base, SessionLocal
from models import User, SpinHistory
from game_engine import RouletteEngine
from security import get_password_hash
from api_routes import router as api_router

# Inicjalizacja bazy danych
Base.metadata.create_all(bind=engine)

# Inicjalizacja aplikacji
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dołączanie routera z endpointami
app.include_router(api_router)

# Silnik gry
game_engine = RouletteEngine()

# Lista aktywnych zakładów
ACTIVE_BETS = []

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        message["server_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()


# WebSocket

CURRENT_GAME_STATE = {"status": "waiting", "time_left": 10}

@app.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "init", 
            "history": list(game_engine.history),
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        while True:
            data_text = await websocket.receive_text()
            data = json.loads(data_text)

            if data.get("type") == "place_bet":
                if CURRENT_GAME_STATE["status"] != "betting":
                    continue
                
                user_id = data.get("user_id")
                amount = float(data.get("amount"))
                bet_type = data.get("bet_type")
                bet_value = data.get("value")
                
                from database import SessionLocal
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.id == user_id).first()
                    if user and user.balance >= amount:
                        user.balance -= amount
                        db.commit()
                        
                        bet_entry = {
                            "user_id": user_id,
                            "bet_type": bet_type,
                            "value": bet_value,
                            "amount": amount
                        }
                        ACTIVE_BETS.append(bet_entry)
                        
                        bet_description = f"{amount} PLN na "
                        if bet_type == "number":
                            bet_description += f"numer {bet_value}"
                        elif bet_type == "color":
                            color_names = {"red": "CZERWONY", "black": "CZARNY", "green": "ZIELONY"}
                            bet_description += color_names.get(bet_value, bet_value)
                        elif bet_type == "parity":
                            parity_names = {"even": "PARZYSTE", "odd": "NIEPARZYSTE"}
                            bet_description += parity_names.get(bet_value, bet_value)
                        elif bet_type == "dozen":
                            bet_description += f"tuzin {bet_value}"
                        
                        await websocket.send_json({
                            "type": "bet_confirmed", 
                            "new_balance": user.balance,
                            "message": f"Przyjęto: {amount} PLN na {bet_value}",
                            "bet_info": bet_description
                        })
                    else:
                        await websocket.send_json({"type": "error", "message": "Brak środków"})
                finally:
                    db.close()

    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def game_loop():
    global ACTIVE_BETS
    while True:
        # Faza obstawiania
        CURRENT_GAME_STATE["status"] = "betting"
        ACTIVE_BETS = []
        
        for i in range(20, -1, -1):
            CURRENT_GAME_STATE["time_left"] = i
            await manager.broadcast({"type": "timer", "value": i, "status": "betting"})
            await asyncio.sleep(1)
        
        # Faza losowania
        CURRENT_GAME_STATE["status"] = "rolling"
        await manager.broadcast({"type": "status", "value": "rolling"})
        await asyncio.sleep(2)
        
        result = game_engine.spin()
        
        from database import SessionLocal
        db = SessionLocal()
        try:
            history_entry = SpinHistory(winning_number=result['number'], color=result['color'])
            db.add(history_entry)
            
            winning_users_updates = {}
            
            # Rozliczanie wielu zakladow
            for bet in ACTIVE_BETS:
                payout = game_engine.calculate_payout(
                    bet["bet_type"], 
                    str(bet["value"]), 
                    bet["amount"], 
                    result["number"]
                )
                if payout > 0:
                    winning_users_updates[bet["user_id"]] = winning_users_updates.get(bet["user_id"], 0) + payout

            for uid, win_amount in winning_users_updates.items():
                user = db.query(User).filter(User.id == uid).first()
                if user:
                    user.balance += win_amount
            
            db.commit()

            await manager.broadcast({
                "type": "result",
                "number": result['number'],
                "color": result['color'],
                "history": list(game_engine.history),
                "winners": winning_users_updates
            })
            
        finally:
            db.close()
        
        await asyncio.sleep(6)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(game_loop())

    #  Automatyczne tworzenie admina
    from database import SessionLocal
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("TWORZENIE KONTA ADMINA")
            hashed_pw = get_password_hash("admin") # Hasło: admin
            # Tworzymy usera z flagą is_admin=True i dużym saldem
            admin = User(
                username="admin", 
                password=hashed_pw, 
                is_admin=True, 
                balance=100000.0
            )
            db.add(admin)
            db.commit()
            print("Konto admina utworzone: Login: admin / Hasło: admin")
        else:
            print("Konto admina już istnieje: Login: admin / Hasło: admin")
    finally:
        db.close()

