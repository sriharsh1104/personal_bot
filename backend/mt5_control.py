from typing import Dict, List, Optional
from datetime import datetime

# Mock data for demonstration
MOCK_ORDERS = [
    {
        "ticket": 12345,
        "symbol": "EURUSD",
        "type": "BUY",
        "volume": 0.1,
        "price": 1.0850,
        "time": datetime.now().isoformat()
    },
    {
        "ticket": 12346,
        "symbol": "GBPUSD",
        "type": "SELL",
        "volume": 0.2,
        "price": 1.2450,
        "time": datetime.now().isoformat()
    }
]

def get_open_orders() -> List[Dict]:
    """
    Get all open orders
    Returns:
        List[Dict]: List of open orders
    """
    # In a real implementation, this would connect to your trading platform
    return MOCK_ORDERS

def cancel_order(ticket: int) -> Dict:
    """
    Cancel an order by ticket number
    Args:
        ticket (int): Order ticket number
    Returns:
        Dict: Result of the cancellation
    """
    # In a real implementation, this would connect to your trading platform
    return {
        "success": True,
        "message": f"Order {ticket} cancelled successfully",
        "ticket": ticket
    }
