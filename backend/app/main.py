from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, models, schemas, database
from app.solana_client import SolanaClient

# Create the FastAPI app
app = FastAPI()

# Initialize database
models.Base.metadata.create_all(bind=database.engine)


@app.post("/wallets/")
def add_wallet(wallet: schemas.Wallet, db: Session = Depends(database.get_db)):
    """API zum Hinzufügen einer neuen Wallet."""
    result = crud.add_wallet(db, wallet)
    if isinstance(result, dict) and result.get("status") == "failure":
        raise HTTPException(status_code=400, detail=result["message"])
    return {"status": "success", "wallet": result.wallet_address}


@app.delete("/wallets/{wallet_id}")
def remove_wallet(wallet_id: int, db: Session = Depends(database.get_db)):
    """API zum Entfernen einer Wallet."""
    result = crud.remove_wallet(db, wallet_id)
    if isinstance(result, dict) and result.get("status") == "failure":
        raise HTTPException(status_code=404, detail=result["message"])
    return {"status": "success", "wallet_id": wallet_id}


@app.get("/wallets/")
def list_wallets(db: Session = Depends(database.get_db)):
    """API zum Abrufen aller Wallets."""
    wallets = crud.get_wallets(db)
    return wallets if wallets else []


@app.get("/wallets/{wallet_id}/details")
def get_wallet_details(wallet_id: int, db: Session = Depends(database.get_db)):
    """API zum Abrufen der Details einer einzelnen Wallet."""
    print(f"Fetching details for wallet ID: {wallet_id}")  # Debugging
    wallet = crud.get_wallet_by_id(db, wallet_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet


@app.put("/wallets/{wallet_id}/set_allocation/")
def set_allocation(wallet_id: int, allocation: schemas.Allocation, db: Session = Depends(database.get_db)):
    """API zum Aktualisieren der Allokation einer Wallet."""
    print(f"Received wallet_id: {wallet_id}, allocation: {allocation.percentage}")  # Debugging
    result = crud.set_allocation(db, wallet_id, allocation.percentage)
    if isinstance(result, dict) and result.get("status") == "failure":
        print(f"Wallet with ID {wallet_id} not found in the database.")  # Debugging
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.post("/set_private_key/")
def set_private_key(data: schemas.PrivateKey):
    """API zum Setzen des privaten Schlüssels."""
    try:
        SolanaClient.set_private_key(data.key)
        return {"status": "success", "message": "Private key set successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set private key: {str(e)}")
