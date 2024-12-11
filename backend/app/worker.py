import asyncio
from app.database import SessionLocal
from app.crud import get_wallets
import traceback

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
        print("Monitoring wallets...")
        while self.running:
            try:
                with SessionLocal() as session:
                    wallets = get_wallets(session)
                    print(f"Fetched wallets: {wallets}")
                    for wallet in wallets:
                        source_wallet = wallet["wallet_address"]
                        allocation = wallet["allocation_percentage"] / 100
                        print(f"Processing wallet: {source_wallet}")
                        await self.process_wallet(source_wallet, allocation)
            except Exception as e:
                # Fehler im Monitoring loggen
                error_details = traceback.format_exc()
                print(f"Error in monitoring loop: {e}")
                print(f"Traceback: {error_details}")
            finally:
                # Sicherstellen, dass der Loop weiterläuft
                await asyncio.sleep(1)


    async def process_wallet(self, source_wallet, allocation):
        """Repliziert alle Transaktionen eines Quell-Wallets auf der eigenen Wallet."""
        try:
            # Guthaben des Quell-Wallets abrufen
            source_balance = self.client.get_balance(source_wallet)
            if source_balance <= 0:
                print(f"Source wallet {source_wallet} has insufficient balance.")
                return

            # Letzte Transaktionen des Quell-Wallets abrufen
            transactions = self.client.get_recent_transactions(source_wallet)
            if not transactions:
                print(f"No recent transactions for wallet {source_wallet}.")
                return

            for tx in transactions:
                # Details der Transaktion abrufen
                signature = tx["signature"]
                transaction_details = self.client.get_transaction_details(signature)
        
                if transaction_details:
                    for instruction in transaction_details["instructions"]:
                        recipient = instruction.get("recipient")
                        amount = instruction.get("amount")  # Betrag der Transaktion
                        token = instruction.get("token")  # Wenn SPL-Tokens involviert sind

                        if recipient and amount:
                            # Berechnung des Anteils
                            percentage_of_source_balance = amount / source_balance
                        
                            # Guthaben des kopierenden Wallets abrufen
                            own_balance = self.client.get_balance(self.client.keypair.pubkey())
                            if own_balance <= 0:
                                print("Insufficient balance in own wallet. Skipping transaction.")
                                return
                        
                            # Positionsgröße berechnen
                            position_size = own_balance * allocation * percentage_of_source_balance
                            print(f"Calculated position size: {position_size} SOL for recipient {recipient}")

                            # Transaktion ausführen
                            if token:
                                await self.execute_token_transaction(recipient, token, position_size)
                            else:
                                await self.execute_transaction(recipient, position_size)
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
