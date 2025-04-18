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

  return (
    <div className="app">
      <h1>Telegram Channel Messages</h1>
      <div className="messages">
        {messages.map((message, index) => (
          <div key={index} className="message-card">
            <div className="message-header">
              <h2>{message.channel}</h2>
              <span className="timestamp">
                {new Date(message.timestamp).toLocaleString()}
              </span>
            </div>
            <div className="message-sender">
              From: {message.sender}
            </div>
            <div className="message-content">
              {message.text}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App
