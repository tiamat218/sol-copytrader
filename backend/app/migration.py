import sys
import os
from sqlalchemy.orm import Session

# Projektwurzelverzeichnis hinzufügen
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Base, engine
from app.models import Wallet

# Tabellen sicherstellen
print("Initialisiere Tabellen...")
Base.metadata.create_all(bind=engine)

# Verbindung zur Datenbank herstellen
db: Session = SessionLocal()

# Wallets mit Standardwerten aktualisieren
wallets = db.query(Wallet).all()
if not wallets:
    print("Keine Wallets in der Datenbank gefunden.")
else:
    for wallet in wallets:
        if wallet.allocation_percentage is None:
            wallet.allocation_percentage = 10.0
        if wallet.active_trades is None:
            wallet.active_trades = 0
        db.commit()

print("Migration abgeschlossen: Standardwerte gesetzt.")
db.close()
