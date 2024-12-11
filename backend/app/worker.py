import asyncio
from app.database import SessionLocal
from app.crud import get_wallets
import traceback

class MonitoringWorker:
    def __init__(self, solana_client):
        self.client = solana_client
        self.running = False
        self.subscribed_wallets = set()

    async def start(self):
        if self.running:
            print("Monitoring worker already running.")
            return

        self.running = True
        asyncio.create_task(self.monitor_wallets())
        print("Monitoring worker started.")

    async def stop(self):
        self.running = False
        print("Monitoring worker stopped.")

    async def monitor_wallets(self):
        while self.running:
            try:
                with SessionLocal() as session:
                    wallets = get_wallets(session)
                    for wallet in wallets:
                        wallet_address = wallet["wallet_address"]
                        allocation = wallet["allocation_percentage"] / 100
                        # Check if already subscribed
                        if wallet_address not in self.subscribed_wallets:
                            asyncio.create_task(self.subscribe_and_monitor(wallet_address, allocation))
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                traceback.print_exc()
            finally:
                await asyncio.sleep(1)

    async def subscribe_and_monitor(self, wallet_address: str, allocation: float):
        try:
            self.subscribed_wallets.add(wallet_address)
            balance = self.client.get_balance(wallet_address)
            print(f"Wallet {wallet_address} Balance: {balance:.4f} SOL")

            await self.client.subscribe_to_transactions(
                wallet_address,
                lambda addr, tx_data: self.handle_transaction(addr, tx_data, allocation)
            )
        except Exception as e:
            print(f"Error monitoring wallet {wallet_address}: {e}")
            self.subscribed_wallets.discard(wallet_address)

    async def handle_transaction(self, wallet_address: str, tx_data: dict, allocation: float):
        try:
            print(f"Transaction Update for {wallet_address}: {tx_data}")

            # Überprüfen, ob `result` ein dict ist
            result = tx_data.get("result")
            if isinstance(result, int):
                print(f"Received an integer result: {result}. No further processing required.")
                return  # Nichts zu tun, wenn `result` nur eine ID oder Ähnliches ist

            if not isinstance(result, dict):
                print(f"Unexpected result type: {type(result)}. Expected dict.")
                return

            # Extrahiere Anweisungen aus der Transaktion
            transaction = result.get("value", {}).get("transaction", {})
            message = transaction.get("message", {})
            instructions = message.get("instructions", [])
            if not instructions:
                print("No valid instructions found in the transaction.")
                return

            # Verarbeite jede Anweisung
            for instruction in instructions:
                accounts = instruction.get("accounts", [])
                if len(accounts) < 2:
                    print(f"Invalid instruction format: {instruction}")
                    continue

                recipient = accounts[1]  # Empfänger
                amount = instruction.get("lamports", 0) / 10**9  # Lamports zu SOL umwandeln

                # Berechne die Positionsgröße basierend auf der Allokation
                source_balance = self.client.get_balance(wallet_address)
                if source_balance <= 0:
                    print(f"Source wallet {wallet_address} has insufficient balance.")
                    return

                own_balance = self.client.get_balance(self.client.keypair.pubkey())
                if own_balance <= 0:
                    print("Insufficient balance in own wallet. Skipping transaction.")
                    return

                position_size = own_balance * allocation * (amount / source_balance)
                print(f"Calculated position size: {position_size} SOL for recipient {recipient}")

                # Führe die Transaktion aus
                if recipient:
                    result = self.client.execute_transaction(recipient, position_size)
                    if result:
                        print(f"Copied transaction: {position_size:.4f} SOL to {recipient}")
                    else:
                        print("Failed to copy transaction.")
        except Exception as e:
            print(f"Error handling transaction for {wallet_address}: {e}")

