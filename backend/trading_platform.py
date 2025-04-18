import MetaTrader5 as mt5
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    format='%(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TradingPlatform:
    def __init__(self, login=None, password=None, server=None):
        self.login = login
        self.password = password
        self.server = server
        self.connected = False
        
    def connect(self):
        """Connect to MetaTrader 5"""
        if not mt5.initialize():
            print("❌ Failed to initialize MT5")
            return False
            
        if not mt5.login(self.login, self.password, self.server):
            print(f"❌ Failed to login to MT5: {mt5.last_error()}")
            mt5.shutdown()
            return False
            
        self.connected = True
        print("✅ Successfully connected to MT5")
        return True
        
    def disconnect(self):
        """Disconnect from MetaTrader 5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("✅ Disconnected from MT5")
            
    def place_order(self, signal):
        """Place an order based on the trading signal"""
        if not self.connected:
            print("❌ Not connected to MT5")
            return False
            
        try:
            # Validate signal
            if not all([signal.get('type'), signal.get('instrument'), 
                       signal.get('entry'), signal.get('sl'), signal.get('tps')]):
                raise ValueError("Invalid signal format")
            
            # Prepare order request
            symbol = signal['instrument']
            order_type = mt5.ORDER_TYPE_BUY if signal['type'].lower() == 'buy' else mt5.ORDER_TYPE_SELL
            price = signal['entry']
            sl = signal['sl'][0]
            tp = signal['tps'][0]
            
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                print(f"❌ Symbol {symbol} not found")
                return False
                
            # Calculate lot size (0.01 lot = 1000 units)
            lot = 0.01  # Default lot size
            
            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 10,
                "magic": 234000,
                "comment": f"Telegram Signal {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"❌ Order failed: {result.comment}")
                return False
                
            print(f"✅ Order placed successfully: {result.comment}")
            return True
            
        except Exception as e:
            print(f"❌ Error placing order: {str(e)}")
            return False
            
    def get_account_info(self):
        """Get account information"""
        if not self.connected:
            print("❌ Not connected to MT5")
            return None
            
        try:
            account_info = mt5.account_info()
            if account_info is None:
                print("❌ Failed to get account info")
                return None
                
            return {
                "balance": account_info.balance,
                "equity": account_info.equity,
                "margin": account_info.margin,
                "free_margin": account_info.margin_free,
                "leverage": account_info.leverage
            }
            
        except Exception as e:
            print(f"❌ Error getting account info: {str(e)}")
            return None 