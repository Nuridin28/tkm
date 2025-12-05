import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Phone, Mail, CheckCircle } from 'lucide-react'
import { sendChatMessage, createTicketFromChat } from '../services/api'
import '../styles/AIChat.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

interface AIChatProps {
  contactInfo: {
    phone: string
    email: string
  }
}

export default function AIChat({ contactInfo }: AIChatProps) {
  const { t } = useTranslation()
  
  // Загружаем историю из localStorage при монтировании
  const loadHistory = (): Message[] => {
    const saved = localStorage.getItem(`chat_history_${contactInfo.phone}`)
    if (saved) {
      try {
        return JSON.parse(saved)
      } catch {
        return []
      }
    }
    return [
      {
        role: 'assistant',
        content: t('support.greeting'),
        timestamp: new Date().toISOString()
      }
    ]
  }

  const [messages, setMessages] = useState<Message[]>(loadHistory)
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [ticketCreated, setTicketCreated] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Обновляем приветственное сообщение при смене языка
  useEffect(() => {
    const saved = localStorage.getItem(`chat_history_${contactInfo.phone}`)
    if (!saved && messages.length === 1 && messages[0].role === 'assistant') {
      // Если только приветственное сообщение, обновляем его при смене языка
      setMessages([{
        role: 'assistant',
        content: t('support.greeting'),
        timestamp: new Date().toISOString()
      }])
    }
  }, [t, contactInfo.phone])

  // Сохраняем историю в localStorage при изменении
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem(`chat_history_${contactInfo.phone}`, JSON.stringify(messages))
    }
  }, [messages, contactInfo.phone])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputMessage.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: inputMessage.trim()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setLoading(true)

    try {
      // Отправляем сообщение в API
      const response = await sendChatMessage({
        message: userMessage.content,
        conversation_history: messages.map(msg => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp
        })),
        contact_info: contactInfo
      })

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString()
      }

      setMessages(prev => [...prev, assistantMessage])

      // Если нужно создать тикет
      if (response.should_create_ticket && response.ticket_draft && !ticketCreated) {
        try {
          // Добавляем всю историю чата в драфт тикета
          const fullHistory = [...messages, userMessage, assistantMessage]
          const ticketDraftWithHistory = {
            ...response.ticket_draft,
            conversation_history: fullHistory.map(msg => ({
              role: msg.role,
              content: msg.content,
              timestamp: msg.timestamp || new Date().toISOString()
            }))
          }
          
          await createTicketFromChat(ticketDraftWithHistory)
          setTicketCreated(true)
          
          const ticketMessage: Message = {
            role: 'assistant',
            content: t('support.ticketSent'),
            timestamp: new Date().toISOString()
          }
          
          setTimeout(() => {
            setMessages(prev => [...prev, ticketMessage])
          }, 1000)
        } catch (error) {
          console.error('Ошибка при создании тикета:', error)
        }
      }
    } catch (error) {
      console.error('Ошибка при отправке сообщения:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: t('support.error'),
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="ai-chat">
      <div className="chat-header">
        <h2>{t('support.chatTitle')}</h2>
        <div className="contact-info">
          <span className="contact-item">
            <Phone size={16} />
            {contactInfo.phone}
          </span>
          {contactInfo.email && (
            <span className="contact-item">
              <Mail size={16} />
              {contactInfo.email}
            </span>
          )}
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
          >
            <div className="message-content">
              {message.content}
            </div>
            {message.timestamp && (
              <div className="message-time">
                {new Date(message.timestamp).toLocaleTimeString('ru-RU', {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="message assistant-message">
            <div className="message-content">
              <span className="typing-indicator">{t('support.typing')}</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="chat-input-form">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder={t('support.chatPlaceholder')}
          disabled={loading || ticketCreated}
          className="chat-input"
        />
        <button
          type="submit"
          disabled={loading || !inputMessage.trim() || ticketCreated}
          className="send-button"
          style={{ color: 'white', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
        >
          {t('support.send')}
        </button>
      </form>

      {ticketCreated && (
        <div className="ticket-notification">
          <CheckCircle size={20} />
          <span>{t('support.ticketCreated')}</span>
        </div>
      )}
    </div>
  )
}

