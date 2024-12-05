from sqlalchemy import Column, Integer, String, Float
from .database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String, unique=True, index=True)
    pnl = Column(Float, default=0.0)
    active_trades = Column(Integer, default=0)  # Standardwert für active_trades
    allocation_percentage = Column(Float, default=10.0)  # Standardwert für allocation_percentage
