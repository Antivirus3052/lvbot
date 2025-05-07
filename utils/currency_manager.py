import json
import os
from typing import Dict, Optional, Union

class CurrencyManager:
    """Manages user currency balances and transactions"""
    
    def __init__(self, currency_file='user_balances.json'):
        self.currency_file = currency_file
        self.balances = self._load_balances()
        
    def _load_balances(self) -> Dict[str, float]:
        """Load user balances from file"""
        if os.path.exists(self.currency_file):
            try:
                with open(self.currency_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading balances: {e}")
                return {}
        return {}
    
    def _save_balances(self) -> None:
        """Save user balances to file"""
        try:
            with open(self.currency_file, 'w') as f:
                json.dump(self.balances, f, indent=4)
        except Exception as e:
            print(f"Error saving balances: {e}")
    
    def get_balance(self, user_id: str) -> float:
        """Get a user's current balance"""
        return float(self.balances.get(str(user_id), 0))
    
    def add_balance(self, user_id: str, amount: float) -> float:
        """Add to a user's balance"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
            
        user_id = str(user_id)
        current = self.get_balance(user_id)
        new_balance = current + amount
        self.balances[user_id] = new_balance
        self._save_balances()
        return new_balance
    
    def remove_balance(self, user_id: str, amount: float) -> float:
        """Remove from a user's balance"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
            
        user_id = str(user_id)
        current = self.get_balance(user_id)
        
        if current < amount:
            raise ValueError("Insufficient balance")
            
        new_balance = current - amount
        self.balances[user_id] = new_balance
        self._save_balances()
        return new_balance
    
    def has_sufficient_balance(self, user_id: str, amount: float) -> bool:
        """Check if user has sufficient balance for a transaction"""
        return self.get_balance(user_id) >= amount
    
    def transfer(self, from_user_id: str, to_user_id: str, amount: float) -> Dict[str, float]:
        """Transfer currency from one user to another"""
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
            
        from_user_id, to_user_id = str(from_user_id), str(to_user_id)
        
        # Check if sender has sufficient funds
        if not self.has_sufficient_balance(from_user_id, amount):
            raise ValueError("Insufficient balance for transfer")
        
        # Remove from sender
        from_balance = self.remove_balance(from_user_id, amount)
        
        # Add to receiver
        to_balance = self.add_balance(to_user_id, amount)
        
        return {
            "from_balance": from_balance,
            "to_balance": to_balance
        }
    
    def process_purchase(self, user_id: str, seller_id: str, amount: float) -> Dict[str, Union[bool, float, str]]:
        """Process a purchase transaction"""
        user_id, seller_id = str(user_id), str(seller_id)
        
        try:
            if not self.has_sufficient_balance(user_id, amount):
                return {
                    "success": False,
                    "error": "Insufficient balance",
                    "user_balance": self.get_balance(user_id)
                }
            
            # Transfer funds from buyer to seller
            balances = self.transfer(user_id, seller_id, amount)
            
            return {
                "success": True,
                "user_balance": balances["from_balance"],
                "seller_balance": balances["to_balance"],
                "amount": amount
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_balance": self.get_balance(user_id)
            }