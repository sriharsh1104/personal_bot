from telethon import TelegramClient, events
import asyncio
import logging
from dotenv import load_dotenv
import os
from datetime import datetime
import websockets
import json
import re
from trading_platform import TradingPlatform

# Configure logging
logging.basicConfig(
    format='%(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')

# Trading Platform credentials
MT5_LOGIN = os.getenv('MT5_LOGIN')
MT5_PASSWORD = os.getenv('MT5_PASSWORD')
MT5_SERVER = os.getenv('MT5_SERVER')

# Channel usernames
CHANNELS = [
    'goldhunterpaulnow',  # GOLDHUNTER🦁| PAUL FX 🇳🇱
    # 'Traderjamessss'      # TRADER JAMES
]

# Initialize trading platform
trading_platform = TradingPlatform(
    login=MT5_LOGIN,
    password=MT5_PASSWORD,
    server=MT5_SERVER
)

# Connect to MT5
if not trading_platform.connect():
    print("❌ Failed to connect to MT5. Please check your credentials.")
    exit(1)

# WebSocket connections
connected_clients = set()

async def register(websocket):
    connected_clients.add(websocket)
    print(f"📱 New client connected (Total: {len(connected_clients)})")

async def unregister(websocket):
    connected_clients.remove(websocket)
    print(f"📱 Client disconnected (Total: {len(connected_clients)})")

async def broadcast_message(message_data):
    """Broadcast message to all connected clients"""
    if connected_clients:
        message = json.dumps(message_data)
        await asyncio.gather(
            *[client.send(message) for client in connected_clients]
        )

def print_message(chat_title, sender_name, message_text, message_date):
    """Print message in a formatted way"""
    print("\n" + "="*50)
    print(f"📢 Channel: {chat_title}")
    print(f"⏰ Time: {message_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 From: {sender_name}")
    print("-"*50)
    print(f"💬 Message: {message_text}")
    print("="*50 + "\n")

async def get_last_messages(client, channel, limit=300):
    """Fetch last messages from a channel and check for trading signals"""
    try:
        print(f"\n📡 Fetching last {limit} messages from {channel.title}...")
        print(f"🔍 Channel ID: {channel.id}")
        print(f"🔍 Channel username: {channel.username}")
        print(f"🔍 Channel access hash: {channel.access_hash}")
        
        messages = await client.get_messages(channel, limit=limit)
        print(f"✅ Found {len(messages)} messages")
        
        # Counters for different types of signals
        buy_signals_count = 0
        sell_signals_count = 0
        total_signals_count = 0
        
        print("\n🔍 Starting to scan messages for trading signals...")
        
        for message in messages:
            # Get sender information safely
            sender_name = "Channel Admin"
            if message.sender:
                if hasattr(message.sender, 'first_name'):
                    sender_name = f"{message.sender.first_name} {message.sender.last_name or ''}".strip()
                elif hasattr(message.sender, 'title'):
                    sender_name = message.sender.title
                elif hasattr(message.sender, 'username'):
                    sender_name = f"@{message.sender.username}"
            
            if message.text:  # Only process messages with text content
                # Parse trading signal
                trading_signal = parse_trading_signal(message.text)
                
                if trading_signal:
                    total_signals_count += 1
                    if trading_signal['type'] == 'buy':
                        buy_signals_count += 1
                    else:
                        sell_signals_count += 1
                    
                    print("\n" + "="*50)
                    print("🎯 FOUND TRADING SIGNAL!")
                    print(f"📅 Date: {message.date.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"👤 From: {sender_name}")
                    print(f"📊 Type: {trading_signal['type'].upper()}")
                    print(f"💰 Instrument: {trading_signal['instrument']}")
                    print(f"🎯 Entry: {trading_signal['entry']}")
                    print(f"🛑 SL: {', '.join(map(str, trading_signal['sl']))}")
                    print(f"🎯 TPs: {', '.join(map(str, trading_signal['tps']))}")
                    print("="*50 + "\n")
                    print("Original Message:")
                    print(message.text)
                    print("="*50 + "\n")
                
                message_data = {
                    "channel": channel.title,
                    "sender": sender_name,
                    "text": message.text,
                    "timestamp": message.date.isoformat(),
                    "is_trading_signal": trading_signal is not None,
                    "trading_signal": trading_signal
                }
                await broadcast_message(message_data)
            else:
                print("⚠️ Message has no text content (might be media only)")
        
        print("\n📊 Signal Analysis Summary:")
        print(f"Total Messages Scanned: {len(messages)}")
        print(f"Total Trading Signals Found: {total_signals_count}")
        print(f"BUY Signals: {buy_signals_count}")
        print(f"SELL Signals: {sell_signals_count}")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"❌ Error getting messages from {channel.title}: {str(e)}")
        print("⚠️ Please check if you have access to this channel")

async def websocket_handler(websocket, path):
    await register(websocket)
    try:
        # Send a welcome message
        await websocket.send(json.dumps({
            "type": "system",
            "message": "Connected to Telegram bot server"
        }))
        
        # Keep the connection alive
        async for message in websocket:
            try:
                # Handle incoming messages if needed
                data = json.loads(message)
                print(f"📥 Received from client: {data}")
            except json.JSONDecodeError:
                print("⚠️ Received invalid JSON from client")
    except websockets.exceptions.ConnectionClosed:
        print("⚠️ Client connection closed unexpectedly")
    finally:
        await unregister(websocket)

def parse_trading_signal(message_text):
    """Parse trading signals from message text"""
    # Split message into lines and clean them
    lines = [line.strip() for line in message_text.split('\n') if line.strip()]
    
    # Check if message follows the expected format
    if len(lines) < 3:  # At least need instrument, entry, and one TP
        return None

    # Initialize signal data
    signal = {
        "type": None,  # buy or sell
        "instrument": None,
        "entry": None,
        "sl": [],  # Changed to array to handle multiple SL values
        "tps": []
    }

    # Parse first line for instrument, type, and possibly entry
    first_line = lines[0].lower()
    
    # Check for instrument
    if 'gold' in first_line or 'xauusd' in first_line:
        signal["instrument"] = "XAUUSD" if 'xauusd' in first_line else "Gold"
    
    # Check for type and extract entry if present
    if 'buy' in first_line:
        signal["type"] = "buy"
        # Try to extract entry from first line
        try:
            # Look for numbers after 'buy'
            numbers = re.findall(r'\d+\.?\d*', first_line.split('buy')[1])
            if numbers:
                signal["entry"] = float(numbers[0])
        except (ValueError, IndexError):
            pass
    elif 'sell' in first_line:
        signal["type"] = "sell"
        # Try to extract entry from first line
        try:
            # Look for numbers after 'sell'
            numbers = re.findall(r'\d+\.?\d*', first_line.split('sell')[1])
            if numbers:
                signal["entry"] = float(numbers[0])
        except (ValueError, IndexError):
            pass

    # Parse remaining lines
    for line in lines[1:]:
        line = line.lower()
        # Extract entry price if not found in first line
        if line.startswith('entry') and signal["entry"] is None:
            try:
                signal["entry"] = float(line.split('entry')[1].strip())
            except (ValueError, IndexError):
                pass
        # Extract stop loss (can have multiple values)
        elif line.startswith('sl'):
            try:
                sl_values = line.split('sl')[1].strip().split()
                for sl_value in sl_values:
                    signal["sl"].append(float(sl_value))
            except (ValueError, IndexError):
                pass
        # Extract take profits
        elif line.startswith('tp'):
            try:
                tp_value = float(line.split('tp')[1].strip())
                signal["tps"].append(tp_value)
            except (ValueError, IndexError):
                pass

    # If entry is still not found, try to find it in any line
    if signal["entry"] is None:
        for line in lines:
            try:
                # Look for a number that could be an entry price
                numbers = re.findall(r'\d+\.?\d*', line)
                if numbers:
                    potential_entry = float(numbers[0])
                    # If this is a reasonable price for XAUUSD/Gold
                    if 1000 < potential_entry < 10000:
                        signal["entry"] = potential_entry
                        break
            except ValueError:
                pass

    # Sort values appropriately
    if signal["type"] == "buy":
        signal["sl"].sort()  # Ascending for buy
        signal["tps"].sort()  # Ascending for buy
    else:  # sell
        signal["sl"].sort(reverse=True)  # Descending for sell
        signal["tps"].sort(reverse=True)  # Descending for sell

    # Only return signal if we have all required components
    if (signal["type"] and 
        signal["instrument"] and 
        signal["entry"] is not None and 
        signal["sl"] and  # At least one SL value
        signal["tps"]):
        return signal
    return None

async def handle_new_message(event):
    # Get the chat where the message was sent
    chat = await event.get_chat()
    print(f"\n📩 New message from channel: {chat.title}")
    
    # Get the sender of the message
    sender_name = "Channel Admin"
    if event.message.sender:
        if hasattr(event.message.sender, 'first_name'):
            sender_name = f"{event.message.sender.first_name} {event.message.sender.last_name or ''}".strip()
        elif hasattr(event.message.sender, 'title'):
            sender_name = event.message.sender.title
        elif hasattr(event.message.sender, 'username'):
            sender_name = f"@{event.message.sender.username}"
    
    # Parse trading signal if present
    trading_signal = parse_trading_signal(event.message.text)
    
    # Create message data for frontend
    message_data = {
        "channel": chat.title,
        "sender": sender_name,
        "text": event.message.text,
        "timestamp": event.message.date.isoformat(),
        "is_trading_signal": trading_signal is not None,
        "trading_signal": trading_signal
    }
    
    # If it's a trading signal, try to place the order
    if trading_signal:
        print("\n🎯 Attempting to place order based on signal...")
        order_placed = trading_platform.place_order(trading_signal)
        if order_placed:
            message_data["order_status"] = "success"
        else:
            message_data["order_status"] = "failed"
    
    # Print the message in a formatted way
    print_message(
        chat_title=chat.title,
        sender_name=sender_name,
        message_text=event.message.text,
        message_date=event.message.date
    )
    
    # Broadcast to all connected clients
    await broadcast_message(message_data)

async def main():
    print("\n🚀 Starting Telegram Bot...")
    
    # Create the client
    client = TelegramClient('session_name', API_ID, API_HASH)
    
    try:
        print("🔑 Connecting to Telegram...")
        await client.start(phone=PHONE)
        print("✅ Successfully connected to Telegram!")
        
        # Start WebSocket server with more robust configuration
        print("\n🌐 Starting WebSocket server...")
        websocket_server = await websockets.serve(
            websocket_handler,
            "0.0.0.0",
            8765,
            ping_interval=30,  # Send ping every 30 seconds
            ping_timeout=10,   # Wait 10 seconds for pong
            close_timeout=10,  # Wait 10 seconds before closing
            max_size=2**20    # 1MB max message size
        )
        print("✅ WebSocket server started on ws://0.0.0.0:8765")
        
        # Get the channel entities
        channels = []
        for channel_username in CHANNELS:
            try:
                print(f"\n📡 Connecting to channel: {channel_username}")
                # Try to get the channel by its username
                try:
                    channel = await client.get_entity(channel_username)
                except ValueError:
                    # If that fails, try with the @ symbol
                    try:
                        channel = await client.get_entity(f"@{channel_username}")
                    except ValueError:
                        # If that fails, try to get the channel by invite link
                        try:
                            # First try without @
                            channel = await client.get_entity(f"https://t.me/{channel_username}")
                        except ValueError:
                            # Then try with @
                            channel = await client.get_entity(f"https://t.me/@{channel_username}")
                
                channels.append(channel)
                print(f"✅ Connected to channel: {channel.title}")
                print(f"🔍 Channel ID: {channel.id}")
                print(f"🔍 Channel username: {channel.username}")
                print(f"🔍 Channel access hash: {channel.access_hash}")
                
                # Fetch last messages from this channel
                await get_last_messages(client, channel)
                
            except Exception as e:
                print(f"❌ Failed to connect to channel {channel_username}: {str(e)}")
                print("⚠️ Please make sure you are a member of this channel and the username is correct")
        
        if not channels:
            print("❌ No channels found. Please check the channel usernames and make sure you are a member.")
            return
        
        print(f"\n✅ Successfully connected to {len(channels)} channels")
        
        @client.on(events.NewMessage(chats=channels))
        async def handle_new_message(event):
            await handle_new_message(event)
        
        # Keep the script running
        print("\n🎯 Bot is now running and monitoring channels...")
        print("Press Ctrl+C to stop.\n")
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        print("⚠️ Please check your credentials and internet connection")

if __name__ == '__main__':
    asyncio.run(main()) 