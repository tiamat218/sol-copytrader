from solana.rpc.api import Client

class SolanaClient:
    client = Client("https://api.mainnet-beta.solana.com")
    private_key = None

    @staticmethod
    def set_private_key(key: str):
        SolanaClient.private_key = key

    @staticmethod
    def monitor_wallet(wallet_address):
        # Placeholder: implement transaction tracking logic
        return f"Monitoring wallet: {wallet_address}"
