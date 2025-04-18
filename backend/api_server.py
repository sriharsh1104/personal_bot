from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class Message(BaseModel):
    channel: str
    sender: str
    text: str
    timestamp: str

# Store messages in memory (you can replace this with a database later)
messages: List[Message] = []

@app.get("/messages")
async def get_messages():
    return messages

@app.post("/messages")
async def add_message(message: Message):
    messages.append(message)
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 