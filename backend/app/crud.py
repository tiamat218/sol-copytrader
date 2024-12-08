from sqlalchemy.orm import Session
from .models import Wallet


def add_wallet(db: Session, wallet):
    """Fügt eine neue Wallet zur Datenbank hinzu."""
    existing_wallet = db.query(Wallet).filter(Wallet.wallet_address == wallet.wallet_address).first()
    if existing_wallet:
        return {"status": "failure", "message": "Wallet address already exists."}
    db_wallet = Wallet(wallet_address=wallet.wallet_address, allocation_percentage=10.0, active_trades=0)
    db.add(db_wallet)
    db.commit()
    db.refresh(db_wallet)
    return {"status": "success", "wallet": {
        "id": db_wallet.id,
        "wallet_address": db_wallet.wallet_address,
        "allocation_percentage": db_wallet.allocation_percentage,
        "active_trades": db_wallet.active_trades,
        "pnl": db_wallet.pnl
    }}


def remove_wallet(db: Session, wallet_id: int):
    """Entfernt eine Wallet anhand ihrer ID."""
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if wallet:
        db.delete(wallet)
        db.commit()
        return {"status": "success", "wallet_id": wallet_id}
    return {"status": "failure", "message": "Wallet not found"}


def get_wallets(db: Session):
    """Gibt alle Wallets in der Datenbank zurück."""
    wallets = db.query(Wallet).all()
    return [
        {
            "id": wallet.id,
            "wallet_address": wallet.wallet_address,
            "pnl": wallet.pnl,
            "active_trades": wallet.active_trades if wallet.active_trades is not None else 0,
            "allocation_percentage": wallet.allocation_percentage if wallet.allocation_percentage is not None else 10.0,
        }
        for wallet in wallets
    ]


def get_wallet_by_id(db: Session, wallet_id: int):
    """Gibt die Details einer Wallet anhand ihrer ID zurück."""
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if wallet:
        return {
            "id": wallet.id,
            "wallet_address": wallet.wallet_address,
            "pnl": wallet.pnl,
            "active_trades": wallet.active_trades if wallet.active_trades is not None else 0,
            "allocation_percentage": wallet.allocation_percentage if wallet.allocation_percentage is not None else 10.0,
        }
    return {"status": "failure", "message": "Wallet not found"}


def set_allocation(db: Session, wallet_id: int, allocation: float):
    """Setzt den Allokationsprozentsatz für eine Wallet."""
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if wallet:
        wallet.allocation_percentage = allocation
        db.commit()
        db.refresh(wallet)
        return {
            "status": "success",
            "wallet_id": wallet.id,
            "allocation_percentage": wallet.allocation_percentage
        }
    return {"status": "failure", "message": "Wallet not found"}


def update_wallet_pnl(db: Session, wallet_id: int, pnl: float):
    """Aktualisiert den PnL (Profit and Loss) einer Wallet."""
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if wallet:
        wallet.pnl = pnl
        db.commit()
        db.refresh(wallet)
        return {
            "status": "success",
            "wallet_id": wallet.id,
            "pnl": wallet.pnl
        }
    return {"status": "failure", "message": "Wallet not found"}


def update_wallet_active_trades(db: Session, wallet_id: int, active_trades: int):
    """Aktualisiert die Anzahl aktiver Trades einer Wallet."""
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if wallet:
        wallet.active_trades = active_trades
        db.commit()
        db.refresh(wallet)
        return {
            "status": "success",
            "wallet_id": wallet.id,
            "active_trades": wallet.active_trades
        }
    return {"status": "failure", "message": "Wallet not found"}
