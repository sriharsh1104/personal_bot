from telethon import TelegramClient, events
import asyncio
import logging
from dotenv import load_dotenv
import os
from datetime import datetime
import websockets
import json

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

# Channel usernames
CHANNELS = [
    'goldhunterpaulnow',  # GOLDHUNTER🦁| PAUL FX 🇳🇱
    # 'Traderjamessss'      # TRADER JAMES
]

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

async def get_last_messages(client, channel, limit=5):
    """Fetch last messages from a channel"""
    try:
        print(f"\n📡 Fetching last {limit} messages from {channel.title}...")
        print(f"🔍 Channel ID: {channel.id}")
        print(f"🔍 Channel username: {channel.username}")
        print(f"🔍 Channel access hash: {channel.access_hash}")
        
        messages = await client.get_messages(channel, limit=limit)
        print(f"✅ Found {len(messages)} messages")
        
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
            
            if message.text:  # Only print messages with text content
                print(f"💬 Message content: {message.text[:100]}...")
                message_data = {
                    "channel": channel.title,
                    "sender": sender_name,
                    "text": message.text,
                    "timestamp": message.date.isoformat()
                }
                print_message(
                    chat_title=channel.title,
                    sender_name=sender_name,
                    message_text=message.text,
                    message_date=message.date
                )
                await broadcast_message(message_data)
            else:
                print("⚠️ Message has no text content (might be media only)")
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
                channel = await client.get_entity(channel_username)
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
            
            # Create message data for frontend
            message_data = {
                "channel": chat.title,
                "sender": sender_name,
                "text": event.message.text,
                "timestamp": event.message.date.isoformat()
            }
            
            # Print the message in a formatted way
            print_message(
                chat_title=chat.title,
                sender_name=sender_name,
                message_text=event.message.text,
                message_date=event.message.date
            )
            
            # Broadcast to all connected clients
            await broadcast_message(message_data)
        
        # Keep the script running
        print("\n🎯 Bot is now running and monitoring channels...")
        print("Press Ctrl+C to stop.\n")
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        print("⚠️ Please check your credentials and internet connection")

if __name__ == '__main__':
    asyncio.run(main()) 