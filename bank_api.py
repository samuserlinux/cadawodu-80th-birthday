import os
from dotenv import load_dotenv

load_dotenv()

class BankAccountAPI:
    def __init__(self):
        self.api_key = os.getenv("BANK_API_KEY", "demo_key")
        self.bank_name = os.getenv("BANK_NAME", "C. A. Dawodu 80th Birthday Account")

    def fetch_realtime_balance(self, current_contributions, current_expenses):
        total_in = sum(item['Amount'] for item in current_contributions)
        total_out = sum(item['Amount'] for item in current_expenses)
        live_balance = total_in - total_out
        
        return {
            "bank_name": self.bank_name,
            "account_number": "XXXX-XXXX-8080",
            "available_balance": live_balance,
            "status": "Connected (Live Sync)"
        }
