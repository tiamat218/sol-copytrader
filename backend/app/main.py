from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, models, schemas, database
from app.worker import MonitoringWorker
from app.routes import router
from app.solana_client import SolanaClient
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from solders.pubkey import Pubkey
import json

# Initialisierung von SolanaClient und MonitoringWorker
solana_client = SolanaClient()
worker = MonitoringWorker(solana_client)

app = FastAPI()

# Router einbinden
app.include_router(router)

# Datenbank initialisieren
models.Base.metadata.create_all(bind=database.engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Verwaltet die Lebensdauer der Anwendung."""
    print("Starting monitoring worker...")
    await worker.start()
    print("Monitoring worker started successfully. Backend is fully operational.")

    yield  # Anwendung läuft hier

    print("Stopping monitoring worker...")
    await worker.stop()
    print("Monitoring worker stopped successfully. Backend is shutting down.")


app = FastAPI(lifespan=lifespan)

@app.post("/wallets/")
async def add_wallet(wallet: schemas.Wallet, db: Session = Depends(database.get_db)):
    """API zum Hinzufügen einer neuen Wallet."""
    result = crud.add_wallet(db, wallet)
    if isinstance(result, dict) and result.get("status") == "failure":
        raise HTTPException(status_code=400, detail=result["message"])
    return {"status": "success", "wallet": result["wallet"]}


@app.delete("/wallets/{wallet_id}")
async def remove_wallet(wallet_id: int, db: Session = Depends(database.get_db)):
    """API zum Entfernen einer Wallet."""
    result = crud.remove_wallet(db, wallet_id)
    if isinstance(result, dict) and result.get("status") == "failure":
        raise HTTPException(status_code=404, detail=result["message"])
    return {"status": "success", "wallet_id": wallet_id}


@app.get("/wallets/")
async def list_wallets(db: Session = Depends(database.get_db)):
    """API zum Abrufen aller Wallets."""
    wallets = crud.get_wallets(db)
    return wallets if wallets else []


@app.put("/wallets/{wallet_id}/set_allocation/")
async def set_allocation(wallet_id: int, allocation: schemas.Allocation, db: Session = Depends(database.get_db)):
    """API zum Aktualisieren der Allokation einer Wallet."""
    result = crud.set_allocation(db, wallet_id, allocation.percentage)
    if isinstance(result, dict) and result.get("status") == "failure":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.post("/set_private_key/")
async def set_private_key(data: dict):
    """Setzt den privaten Schlüssel."""
    private_key = data.get("key")
    if not private_key:
        raise HTTPException(status_code=400, detail="Private key is missing")
    try:
        solana_client.set_private_key(private_key)
        return {"status": "success", "message": "Private key set successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wallets/{wallet_address}/balance/")
async def get_wallet_balance(wallet_address: str):
    """Ruft den Kontostand einer Wallet ab."""
    try:
        balance = solana_client.get_balance(wallet_address)
        if balance is None:
            raise HTTPException(status_code=404, detail="Wallet balance not found.")
        return {"wallet_address": wallet_address, "balance": balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wallets/{wallet_address}/transactions/")
async def get_wallet_transactions(wallet_address: str):
    """Ruft die letzten Transaktionen einer Wallet ab."""
    try:
        transactions = solana_client.get_recent_transactions(wallet_address)
        if not transactions:
            raise HTTPException(status_code=404, detail="No transactions found.")
        return {"wallet_address": wallet_address, "transactions": transactions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/copy_trade/")
async def copy_trade(data: dict):
    """Führt einen Copy-Trade aus."""
    recipient_address = data.get("recipient_wallet")
    allocation_percentage = data.get("allocation_percentage", 0.1)
    if not recipient_address:
        raise HTTPException(status_code=400, detail="Recipient wallet is missing")
    try:
        balance = solana_client.get_balance(solana_client.keypair.pubkey())
        if balance is None or balance <= 0:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        amount = balance * allocation_percentage
        result = solana_client.execute_transaction(recipient_address, amount)
        if result["status"] == "failure":
            raise HTTPException(status_code=500, detail=result["error"])
        return {"status": "success", "tx_id": result["tx_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
