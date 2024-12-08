from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.solana_client import SolanaClient
from app.worker import MonitoringWorker
from app import crud, schemas, database

router = APIRouter()
solana_client = SolanaClient()
worker = MonitoringWorker(solana_client)

@router.post("/set_private_key/")
def set_private_key(data: schemas.PrivateKey):
    """Setzt den privaten Schlüssel."""
    try:
        solana_client.set_private_key(data.key)
        return {"status": "success", "message": "Private key set successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wallets/{wallet_address}/balance/")
def get_wallet_balance(wallet_address: str):
    """Ruft den Kontostand einer Wallet ab."""
    try:
        balance = solana_client.get_balance(wallet_address)
        return {"wallet_address": wallet_address, "balance": balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wallets/")
def list_wallets(db: Session = Depends(database.get_db)):
    """Listet alle Wallets auf."""
    try:
        return crud.get_wallets(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wallets/")
def add_wallet(wallet: schemas.Wallet, db: Session = Depends(database.get_db)):
    """Fügt eine neue Wallet hinzu."""
    try:
        return crud.add_wallet(db, wallet)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
