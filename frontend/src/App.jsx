import React, { useEffect, useState } from "react";
import axios from "axios";

function App() {
  const [orders, setOrders] = useState([]);

  const fetchOrders = async () => {
    const res = await axios.get("http://localhost:8000/orders");
    setOrders(res.data);
  };

  const cancelOrder = async (ticket) => {
    await axios.post(`http://localhost:8000/cancel/${ticket}`);
    fetchOrders();
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  return (
    <div className="p-6 font-sans">
      <h1 className="text-2xl font-bold mb-4">MT5 Bot Dashboard</h1>
      <button onClick={fetchOrders} className="mb-4 px-4 py-2 bg-blue-500 text-white rounded">
        Refresh Orders
      </button>
      <ul>
        {orders.map((order) => (
          <li key={order.ticket} className="mb-2">
            <span className="mr-4">{order.symbol} - {order.type}</span>
            <button onClick={() => cancelOrder(order.ticket)} className="px-2 py-1 bg-red-500 text-white rounded">
              Cancel
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
