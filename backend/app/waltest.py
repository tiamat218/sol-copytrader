from solana_client import SolanaClient

client = SolanaClient()
wallet_address = "ES3vfhTe2PUQxBQz6bmegDTy6u9qERFQZcXrrNnkPnP3"

# Testen der Funktionen
print("Balance:", client.get_balance(wallet_address))
print("Recent Transactions:", client.get_recent_transactions(wallet_address))
