from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.message import Message
from solders.instruction import Instruction
from solders.system_program import transfer, TransferParams
from solders.hash import Hash
from solders.rpc.requests import GetSignaturesForAddress
from solders.transaction_status import EncodedTransactionWithStatusMeta
from solders.transaction import Transaction
from solders.transaction import VersionedTransaction
from solders.rpc.responses import GetTransactionResp
from solders.transaction_status import UiTransaction, UiCompiledInstruction
import base64
import traceback

# Solana RPC-Endpunkt
SOLANA_RPC_URL = "https://api.testnet.solana.com"

class SolanaClient:
    def __init__(self):
        """Initialisiert den Solana-Client."""
        self.client = Client(SOLANA_RPC_URL)
        self.keypair = None

    def set_private_key(self, private_key: str):
        """Setzt den privaten Schlüssel für die eigene Wallet."""
        try:
            secret_key = bytes.fromhex(private_key)
            self.keypair = Keypair.from_secret_key(secret_key)
            if not self.keypair:
                raise ValueError("Invalid keypair generated.")
            print(f"Private key set successfully. Public Key: {self.keypair.pubkey()}")
        except Exception as e:
            print(f"Error setting private key: {e}")
            raise ValueError(f"Invalid private key: {e}")

    def is_valid_pubkey(self, pubkey_str: str) -> bool:
        """Prüft, ob eine Wallet-Adresse gültig ist."""
        try:
            pubkey = Pubkey.from_string(pubkey_str)
            return pubkey.is_on_curve()
        except Exception:
            return False

    def get_balance(self, wallet_address: str):
        """Ruft den Kontostand einer Wallet ab."""
        try:
            if not self.is_valid_pubkey(wallet_address):
                raise ValueError(f"Invalid wallet address: {wallet_address}")

            pubkey = Pubkey.from_string(wallet_address)
            print(f"Querying balance for Pubkey: {pubkey}")

            # RPC-Aufruf
            response = self.client.get_balance(pubkey)
            print(f"Full RPC Response: {response}")  # Loggt die gesamte Antwort

            # Überprüfen der Antwortstruktur
            if hasattr(response, "value") and response.value is not None:
                lamports = response.value
                print(f"Extracted balance in lamports: {lamports}")
                return lamports / 10**9  # Umrechnung von Lamports zu SOL
            else:
                print(f"Unexpected response structure: {response}")
                return 0.0
        except Exception as e:
            print(f"Error in get_balance for {wallet_address}: {e}")
            return 0.0
        
    def get_transaction_details(self, transaction_signature: str) -> dict:
        """Liefert die Details einer Transaktion."""
        try:
            # Abrufen der Transaktionsdaten vom RPC
            response = self.client.get_transaction(transaction_signature)

            if response and response.value:
                transaction_data = response.value.transaction.transaction
                print(f"Transaction data: {transaction_data}")
                print(f"Type of transaction data: {type(transaction_data)}")

                if isinstance(transaction_data, UiTransaction):
                    instructions = []
                    for ui_instruction in transaction_data.message.instructions:
                        instructions.append({
                            "program_id_index": ui_instruction.program_id_index,
                            "accounts": ui_instruction.accounts,
                            "data": ui_instruction.data,
                        })
                    return {"instructions": instructions}

                raise ValueError(f"Unsupported transaction format: {type(transaction_data)}")
            else:
                print("No transaction data found.")
                return None

        except Exception as e:
            # Loggen Sie die vollständige Fehlermeldung und den Stacktrace
            error_details = traceback.format_exc()
            print(f"Error in get_transaction_details: {e}")
            print(f"Traceback: {error_details}")
            return None

    def get_transaction_details(self, transaction_signature: str) -> dict:
        """Liefert die Details einer Transaktion."""
        try:
            # Abrufen der Transaktionsdaten vom RPC
            response: GetTransactionResp = self.client.get_transaction(transaction_signature)

            if response and response.value:
                # Extrahiere die Transaktionsdaten
                transaction_data = response.value.transaction.transaction

                # Verarbeitung von UiTransaction
                if isinstance(transaction_data, UiTransaction):
                    instructions = []
                    for ui_instruction in transaction_data.message.instructions:
                        instructions.append({
                            "program_id_index": ui_instruction.program_id_index,
                            "accounts": ui_instruction.accounts,
                            "data": ui_instruction.data,
                        })
                    return {"instructions": instructions}

                raise ValueError(f"Unsupported transaction format: {type(transaction_data)}")
            else:
                print("No transaction data found.")
                return None
        except Exception as e:
            print(f"Error in get_transaction_details: {e}")
            return None

    def execute_transaction(self, recipient_address: str, amount: float):
        """Führt eine SOL-Transaktion aus."""
        if not self.keypair:
            raise ValueError("Private key not set. Cannot execute transaction.")

        try:
            if not self.is_valid_pubkey(recipient_address):
                raise ValueError(f"Invalid recipient wallet address: {recipient_address}")

            recipient_pubkey = Pubkey.from_string(recipient_address)
            lamports = int(amount * 10**9)  # Konvertiere SOL zu Lamports
            instruction = transfer(
                TransferParams(
                    from_pubkey=self.keypair.pubkey(),
                    to_pubkey=recipient_pubkey,
                    lamports=lamports,
                )
            )

            # Hole die aktuelle Blockhash
            recent_blockhash_resp = self.client.get_recent_blockhash()
            print(f"RPC Response for recent blockhash: {recent_blockhash_resp}")
            if not recent_blockhash_resp or not recent_blockhash_resp.value:
                raise ValueError("Failed to fetch recent blockhash.")
            recent_blockhash = Hash.from_string(recent_blockhash_resp.value.blockhash)

            # Erstellen der Nachricht und der Transaktion
            message = Message([instruction], self.keypair.pubkey())
            transaction = Transaction(message, [self.keypair], recent_blockhash)

            # Senden der Transaktion
            response = self.client.send_transaction(transaction)
            print(f"Transaction Response: {response}")
            if response and response.value is not None:
                return {"status": "success", "tx_id": response.value}
            return {"status": "failure", "error": response.get("error", "Unknown error")}
        except Exception as e:
            print(f"Error in execute_transaction: {e}")
            return {"status": "failure", "error": str(e)}

    async def execute_token_transaction(self, recipient, token, amount):
        """Repliziert eine SPL-Token-Transaktion."""
        if not self.keypair:
            raise ValueError("Private key not set. Cannot execute transaction.")

        try:
            recipient_pubkey = Pubkey.from_string(recipient)
            token_pubkey = Pubkey.from_string(token)
            lamports = int(amount * 10**9)  # Konvertiere Token-Einheiten zu Lamports

            instruction = transfer(
                TransferParams(
                    from_pubkey=self.keypair.pubkey(),
                    to_pubkey=recipient_pubkey,
                    lamports=lamports,
                    program_id=token_pubkey
                )
            )

            # Hole die aktuelle Blockhash
            recent_blockhash_resp = self.client.get_recent_blockhash()
            recent_blockhash = Hash.from_string(recent_blockhash_resp.value.blockhash)

            # Nachricht und Transaktion erstellen
            message = Message([instruction], self.keypair.pubkey())
            transaction = Transaction(message, [self.keypair], recent_blockhash)

            # Senden der Transaktion
            response = self.client.send_transaction(transaction)
            print(f"Token Transaction Response: {response}")
        except Exception as e:
            print(f"Error in execute_token_transaction: {e}")

    def get_recent_transactions(self, wallet_address: str) -> list:
        """Ruft die letzten Transaktionen einer Wallet ab."""
        try:
            pubkey = Pubkey.from_string(wallet_address)
            response = self.client.get_signatures_for_address(pubkey)

            # Überprüfen, ob die Antwort gültig ist
            if response.value:
                transactions = []
                for tx in response.value:
                    transactions.append({
                        "signature": tx.signature,
                        "slot": tx.slot,
                        "err": tx.err,
                        "memo": tx.memo,
                        "block_time": tx.block_time,
                        "confirmation_status": tx.confirmation_status
                    })
                return transactions[:10]
            return []
        except Exception as e:
            print(f"Error in get_recent_transactions for {wallet_address}: {e}")
            return []