import asyncio
import websockets
import json
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.api import Client
from solders.transaction import Transaction
from solders.message import Message
from solders.system_program import transfer, TransferParams
from solders.hash import Hash

SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
WS_URL = "wss://api.mainnet-beta.solana.com"

class SolanaClient:
    def __init__(self):
        self.client = Client(SOLANA_RPC_URL)
        self.keypair = None
        self.subscribed_wallets = set()

    def set_private_key(self, private_key: str):
        try:
            secret_key = bytes.fromhex(private_key)
            self.keypair = Keypair.from_secret_key(secret_key)
            print(f"Private key set successfully. Public Key: {self.keypair.pubkey()}")
        except Exception as e:
            print(f"Error setting private key: {e}")

    def get_balance(self, wallet_address: str):
        try:
            pubkey = Pubkey.from_string(wallet_address)
            response = self.client.get_balance(pubkey)
            return response.value / 10**9 if response.value else 0.0
        except Exception as e:
            print(f"Error fetching balance for {wallet_address}: {e}")
            return 0.0

    async def subscribe_to_transactions(self, wallet_address: str, callback):
        if wallet_address in self.subscribed_wallets:
            print(f"Already subscribed to wallet: {wallet_address}")
            return

        self.subscribed_wallets.add(wallet_address)
        try:
            async with websockets.connect(WS_URL) as websocket:
                subscription_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "accountSubscribe",
                    "params": [wallet_address, {"encoding": "jsonParsed"}]
                }
                await websocket.send(json.dumps(subscription_request))
                print(f"Subscribed to wallet: {wallet_address}")

                while True:
                    response = await websocket.recv()
                    data = json.loads(response)
                    await callback(wallet_address, data)
        except Exception as e:
            print(f"Error in WebSocket subscription for {wallet_address}: {e}")
            self.subscribed_wallets.remove(wallet_address)

    def execute_transaction(self, recipient_address: str, amount: float):
        try:
            recipient_pubkey = Pubkey.from_string(recipient_address)
            lamports = int(amount * 10**9)
            instruction = transfer(
                TransferParams(
                    from_pubkey=self.keypair.pubkey(),
                    to_pubkey=recipient_pubkey,
                    lamports=lamports
                )
            )
            blockhash = self.client.get_recent_blockhash().value.blockhash
            message = Message([instruction], self.keypair.pubkey())
            transaction = Transaction(message, [self.keypair], Hash.from_string(blockhash))
            response = self.client.send_transaction(transaction)
            return response.value if response.value else None
        except Exception as e:
            print(f"Error executing transaction: {e}")
            return None
