import asyncio
from app.database import SessionLocal

class MonitoringWorker:
    def __init__(self, solana_client):
        self.running = False
        self.client = solana_client

    async def start(self):
        """Startet den Monitoring-Worker."""
        if self.running:
            print("Monitoring worker is already running.")
            return

        self.running = True
        print("Monitoring worker starting...")
        asyncio.create_task(self.monitor_wallets())

    async def stop(self):
        """Stoppt den Monitoring-Worker."""
        self.running = False
        print("Stopping monitoring worker...")

    async def monitor_wallets(self):
        """Überwacht Wallets und repliziert Transaktionen."""
        from app.crud import get_wallets  # Lokaler Import, um zirkuläre Abhängigkeit zu vermeiden
        print("Monitoring wallets...")
        while self.running:
            try:
                # Session synchron öffnen und verwenden
                with SessionLocal() as session:
                    wallets = get_wallets(session)
                    print(f"Fetched wallets: {wallets}")
                    for wallet in wallets:
                        source_wallet = wallet["wallet_address"]
                        allocation = wallet["allocation_percentage"] / 100
                        await self.process_wallet(source_wallet, allocation)
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
            await asyncio.sleep(10)

    async def process_wallet(self, source_wallet, allocation):
        """Verarbeitet die Transaktionen eines Quell-Wallets."""
        try:
            transactions = self.client.get_recent_transactions(source_wallet)
            if not transactions:
                print(f"No recent transactions for wallet {source_wallet}.")
                return

            for tx in transactions:
                recipient = tx.get("recipient")  # Angenommene Struktur
                if recipient:
                    await self.execute_transaction(recipient, allocation)
        except Exception as e:
            print(f"Error processing wallet {source_wallet}: {e}")

    async def execute_transaction(self, recipient, allocation):
        """Führt Transaktionen aus."""
        try:
            balance = self.client.get_balance(self.client.keypair.pubkey())
            if balance is None or balance <= 0:
                print("Insufficient balance. Skipping transaction.")
                return

            amount = balance * allocation
            result = self.client.execute_transaction(recipient, amount)
            if result["status"] == "success":
                print(f"Executed transaction: Sent {amount:.2f} SOL to {recipient}")
            else:
                print(f"Transaction failed: {result['error']}")
        except Exception as e:
            print(f"Error in execute_transaction for recipient {recipient}: {e}")
