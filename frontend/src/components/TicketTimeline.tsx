import { useState, useEffect } from 'react'
import { getMessages } from '../services/api'
import '../styles/TicketTimeline.css'

interface TicketTimelineProps {
  ticketId: string
}

export default function TicketTimeline({ ticketId }: TicketTimelineProps) {
  const [messages, setMessages] = useState<any[]>([])

  useEffect(() => {
    loadMessages()
  }, [ticketId])

  const loadMessages = async () => {
    try {
      const data = await getMessages(ticketId)
      setMessages(data)
    } catch (error) {
      console.error('Failed to load messages:', error)
    }
  }

  return (
    <div className="ticket-timeline">
      <h3>История сообщений</h3>
      <div className="timeline-items">
        {messages.map((message) => (
          <div key={message.id} className={`timeline-item ${message.sender_type}`}>
            <div className="timeline-header">
              <span className="sender-type">{message.sender_type}</span>
              <span className="timestamp">{new Date(message.created_at).toLocaleString('ru')}</span>
            </div>
            <div className="timeline-content">{message.text}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

