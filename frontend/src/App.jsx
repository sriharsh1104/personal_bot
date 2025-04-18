import { useState, useEffect, useRef } from 'react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([
    {
      channel: "GOLDHUNTER🦁| PAUL FX 🇳🇱",
      sender: "Paul FX",
      text: "Waiting for messages from Telegram...",
      timestamp: new Date().toISOString()
    },
    {
      channel: "TRADER JAMES",
      sender: "James",
      text: "Waiting for messages from Telegram...",
      timestamp: new Date().toISOString()
    }
  ])
  const [showOnlySignals, setShowOnlySignals] = useState(false)
  const ws = useRef(null)

  useEffect(() => {
    const connectWebSocket = () => {
      // Close existing connection if any
      if (ws.current) {
        ws.current.close()
      }

      // Create new WebSocket connection
      ws.current = new WebSocket('ws://localhost:8765')
      
      ws.current.onopen = () => {
        console.log('✅ Connected to WebSocket server')
      }
      
      ws.current.onmessage = (event) => {
        try {
          const newMessage = JSON.parse(event.data)
          console.log('📩 Received new message:', newMessage)
          
          setMessages(prevMessages => {
            // Check if message already exists
            const messageExists = prevMessages.some(msg => 
              msg.channel === newMessage.channel && 
              msg.text === newMessage.text && 
              msg.timestamp === newMessage.timestamp
            )
            
            if (!messageExists) {
              // Add new message to the beginning of the array
              return [newMessage, ...prevMessages]
            }
            return prevMessages
          })
        } catch (error) {
          console.error('❌ Error parsing message:', error)
        }
      }
      
      ws.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
      }
      
      ws.current.onclose = () => {
        console.log('⚠️ Disconnected from WebSocket server. Reconnecting...')
        // Try to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000)
      }
    }

    // Initial connection
    connectWebSocket()

    // Cleanup on component unmount
    return () => {
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [])

  const filteredMessages = showOnlySignals 
    ? messages.filter(msg => msg.is_trading_signal)
    : messages

  return (
    <div className="app">
      <h1>Telegram Channel Messages</h1>
      <div className="controls">
        <button 
          onClick={() => setShowOnlySignals(!showOnlySignals)}
          className={`filter-button ${showOnlySignals ? 'active' : ''}`}
        >
          {showOnlySignals ? 'Show All Messages' : 'Show Only Trading Signals'}
        </button>
      </div>
      <div className="messages">
        {filteredMessages.map((message, index) => (
          <div 
            key={index} 
            className={`message-card ${message.is_trading_signal ? 'trading-signal' : ''}`}
          >
            <div className="message-header">
              <h2>{message.channel}</h2>
              <span className="timestamp">
                {new Date(message.timestamp).toLocaleString()}
              </span>
            </div>
            <div className="message-sender">
              From: {message.sender}
            </div>
            {message.is_trading_signal ? (
              <div className="trading-signal-content">
                <div className="signal-header">
                  <span className="signal-type">{message.trading_signal.type.toUpperCase()}</span>
                  <span className="signal-instrument">{message.trading_signal.instrument}</span>
                </div>
                <div className="signal-details">
                  <div className="signal-price">
                    <span className="label">Entry:</span>
                    <span className="value">{message.trading_signal.entry}</span>
                  </div>
                  <div className="signal-price">
                    <span className="label">SL:</span>
                    <span className="value">{message.trading_signal.sl}</span>
                  </div>
                  <div className="signal-price">
                    <span className="label">TPs:</span>
                    <div className="tp-values">
                      {message.trading_signal.tps.map((tp, i) => (
                        <span key={i} className="tp-value">{tp}</span>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="original-message">
                  <span className="label">Original Message:</span>
                  <p>{message.text}</p>
                </div>
              </div>
            ) : (
              <div className="message-content">
                {message.text}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default App
