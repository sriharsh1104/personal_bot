from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mt5_control import get_open_orders, cancel_order

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/orders")
def fetch_orders():
    return get_open_orders()

@app.post("/cancel/{ticket}")
def cancel_order_by_ticket(ticket: int):
    return cancel_order(ticket)
