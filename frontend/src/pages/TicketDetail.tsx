import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { MessageCircle, Phone, Mail, Globe, User, History, X } from 'lucide-react'
import { getTicket, acceptTicket, completeRemote, getChatHistory } from '../services/api'
import TicketTimeline from '../components/TicketTimeline'
import AiAssistantPanel from '../components/AiAssistantPanel'
import SLAClock from '../components/SLAClock'
import '../styles/TicketDetail.css'

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [ticket, setTicket] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [showChatHistory, setShowChatHistory] = useState(false)
  const [chatHistory, setChatHistory] = useState<any[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'telegram':
        return <MessageCircle className="w-4 h-4" />
      case 'whatsapp':
        return <Phone className="w-4 h-4" />
      case 'email':
        return <Mail className="w-4 h-4" />
      case 'portal':
      case 'chat':
        return <Globe className="w-4 h-4" />
      case 'phone':
      case 'call_agent':
        return <Phone className="w-4 h-4" />
      default:
        return <User className="w-4 h-4" />
    }
  }

  const getSourceLabel = (source: string) => {
    return t(`tickets.source.${source}`, source)
  }

  useEffect(() => {
    if (id) {
      loadTicket()
    }
  }, [id])

  const loadTicket = async () => {
    try {
      const data = await getTicket(id!)
      setTicket(data)
    } catch (error: any) {
      console.error('Failed to load ticket:', error)
      if (error?.response?.status === 403) {
        alert('У вас нет доступа к этому тикету. Он принадлежит другому департаменту.')
        navigate('/dashboard')
      }
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

  const handleShowChatHistory = async () => {
    setShowChatHistory(true)
    setLoadingHistory(true)
    try {
      const history = await getChatHistory(id!)
      setChatHistory(history)
    } catch (error) {
      console.error('Failed to load chat history:', error)
      setChatHistory([])
    } finally {
      setLoadingHistory(false)
    }
  }

  const handleClassificationUpdate = () => {
    loadTicket()
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
              <span>{t('tickets.status')}: {String(t(`tickets.${ticket.status}`, ticket.status))}</span>
              <span>{t('tickets.priority')}: {String(t(`tickets.${ticket.priority}`, ticket.priority))}</span>
              {ticket.category && (
                <span>
                  {t('tickets.category', 'Категория')}: {ticket.category}
                  {ticket.subcategory && ` / ${ticket.subcategory}`}
                </span>
              )}
              {ticket.source && (
                <span className="flex items-center gap-1">
                  {t('tickets.source.label', 'Источник')}: {getSourceIcon(ticket.source)}
                  {getSourceLabel(ticket.source)}
                </span>
              )}
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
            {(ticket.source === 'chat' || ticket.source === 'portal') && (
              <button onClick={handleShowChatHistory} className="btn-chat-history">
                <History className="btn-icon" />
                История чата
              </button>
            )}
            {ticket.status === 'new' && (
              <button onClick={handleAccept}>Принять тикет</button>
            )}
            {ticket.status === 'accepted' && (
              <button onClick={handleComplete}>Завершить удаленно</button>
            )}
          </div>
        </div>

        <div className="ticket-sidebar">
          <AiAssistantPanel ticket={ticket} onClassificationUpdate={handleClassificationUpdate} />
        </div>
      </div>

      {}
      {showChatHistory && (
        <div className="chat-history-modal" onClick={() => setShowChatHistory(false)}>
          <div className="chat-history-content" onClick={(e) => e.stopPropagation()}>
            <div className="chat-history-header">
              <h2>История чата</h2>
              <button className="close-button" onClick={() => setShowChatHistory(false)}>
                <X className="close-icon" />
              </button>
            </div>
            <div className="chat-history-body">
              {loadingHistory ? (
                <div className="chat-history-loading">Загрузка...</div>
              ) : chatHistory.length === 0 ? (
                <div className="chat-history-empty">История чата не найдена</div>
              ) : (
                <div className="chat-messages">
                  {chatHistory.map((message, index) => (
                    <div
                      key={index}
                      className={`chat-message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
                    >
                      <div className="message-role">
                        {message.role === 'user' ? '👤 Пользователь' : '🤖 Ассистент'}
                      </div>
                      <div className="message-content">{message.content}</div>
                      {message.timestamp && (
                        <div className="message-timestamp">
                          {new Date(message.timestamp).toLocaleString('ru-RU')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

