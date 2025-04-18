import MetaTrader5 as mt5

def get_open_orders():
    if not mt5.initialize():
        return {"error": "MT5 init failed"}
    orders = mt5.orders_get()
    return [order._asdict() for order in orders] if orders else []

def cancel_order(ticket):
    if not mt5.initialize():
        return {"error": "MT5 init failed"}
    request = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": ticket,
    }
    result = mt5.order_send(request)
    return {"result": result}
