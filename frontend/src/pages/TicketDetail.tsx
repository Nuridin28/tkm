import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getTicket, updateTicket, acceptTicket, completeRemote } from '../services/api'
import TicketTimeline from '../components/TicketTimeline'
import AiAssistantPanel from '../components/AiAssistantPanel'
import SLAClock from '../components/SLAClock'
import '../styles/TicketDetail.css'

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [ticket, setTicket] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) {
      loadTicket()
    }
  }, [id])

  const loadTicket = async () => {
    try {
      const data = await getTicket(id!)
      setTicket(data)
    } catch (error) {
      console.error('Failed to load ticket:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAccept = async () => {
    try {
      await acceptTicket(id!)
      await loadTicket()
    } catch (error) {
      console.error('Failed to accept ticket:', error)
    }
  }

  const handleComplete = async () => {
    try {
      await completeRemote(id!)
      await loadTicket()
    } catch (error) {
      console.error('Failed to complete ticket:', error)
    }
  }

  if (loading) {
    return <div className="loading">Загрузка...</div>
  }

  if (!ticket) {
    return <div>Тикет не найден</div>
  }

  return (
    <div className="ticket-detail">
      <header className="ticket-header">
        <button onClick={() => navigate(-1)}>← Назад</button>
        <h1>{ticket.subject}</h1>
      </header>

      <div className="ticket-content">
        <div className="ticket-main">
          <div className="ticket-info">
            <SLAClock ticket={ticket} />
            <div className="ticket-meta">
              <span>Статус: {ticket.status}</span>
              <span>Приоритет: {ticket.priority}</span>
              <span>Категория: {ticket.category}</span>
            </div>
            <div className="ticket-description">
              <h3>Описание</h3>
              <p>{ticket.description}</p>
              {ticket.summary && (
                <div className="ticket-summary">
                  <h4>Резюме (ИИ)</h4>
                  <p>{ticket.summary}</p>
                </div>
              )}
            </div>
          </div>

          <TicketTimeline ticketId={id!} />

          <div className="ticket-actions">
            {ticket.status === 'new' && (
              <button onClick={handleAccept}>Принять тикет</button>
            )}
            {ticket.status === 'accepted' && (
              <button onClick={handleComplete}>Завершить удаленно</button>
            )}
          </div>
        </div>

        <div className="ticket-sidebar">
          <AiAssistantPanel ticket={ticket} />
        </div>
      </div>
    </div>
  )
}

