import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Phone, Mail, CheckCircle } from 'lucide-react'
import { sendChatMessage, createTicketFromChat } from '../services/api'
import '../styles/AIChat.css'

// Простая функция для форматирования Markdown в HTML
function formatMarkdown(text: string): string {
  if (!text) return ''
  
  // Удаляем технические метаданные
  text = text.replace(/CONFIDENCE:\s*[\d.]+\s*/gi, '')
  text = text.replace(/NEEDS_TICKET:\s*(true|false)\s*/gi, '')
  text = text.replace(/REASON:\s*[^\n]*/gi, '')
  text = text.trim()
  
  // Разбиваем на строки
  const lines = text.split('\n')
  const result: string[] = []
  let inOrderedList = false
  let inUnorderedList = false
  let inParagraph = false
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    
    // Пропускаем пустые строки
    if (!line) {
      if (inOrderedList) {
        result.push('</ol>')
        inOrderedList = false
      }
      if (inUnorderedList) {
        result.push('</ul>')
        inUnorderedList = false
      }
      if (inParagraph) {
        result.push('</p>')
        inParagraph = false
      }
      continue
    }
    
    // Заголовки
    if (line.startsWith('## ')) {
      if (inParagraph) result.push('</p>')
      if (inOrderedList) { result.push('</ol>'); inOrderedList = false }
      if (inUnorderedList) { result.push('</ul>'); inUnorderedList = false }
      result.push(`<h2>${line.substring(3)}</h2>`)
      inParagraph = false
      continue
    }
    if (line.startsWith('### ')) {
      if (inParagraph) result.push('</p>')
      if (inOrderedList) { result.push('</ol>'); inOrderedList = false }
      if (inUnorderedList) { result.push('</ul>'); inUnorderedList = false }
      result.push(`<h3>${line.substring(4)}</h3>`)
      inParagraph = false
      continue
    }
    
    // Нумерованные списки
    const numberedMatch = line.match(/^(\d+)\.\s+(.+)$/)
    if (numberedMatch) {
      if (inParagraph) { result.push('</p>'); inParagraph = false }
      if (inUnorderedList) { result.push('</ul>'); inUnorderedList = false }
      if (!inOrderedList) {
        result.push('<ol>')
        inOrderedList = true
      }
      let content = numberedMatch[2]
      // Обрабатываем форматирование внутри списка
      content = content.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      content = content.replace(/\*(.+?)\*/g, '<em>$1</em>')
      content = content.replace(/`(.+?)`/g, '<code>$1</code>')
      result.push(`<li>${content}</li>`)
      continue
    }
    
    // Маркированные списки
    const bulletMatch = line.match(/^[-*]\s+(.+)$/)
    if (bulletMatch) {
      if (inParagraph) { result.push('</p>'); inParagraph = false }
      if (inOrderedList) { result.push('</ol>'); inOrderedList = false }
      if (!inUnorderedList) {
        result.push('<ul>')
        inUnorderedList = true
      }
      let content = bulletMatch[1]
      // Обрабатываем форматирование внутри списка
      content = content.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      content = content.replace(/\*(.+?)\*/g, '<em>$1</em>')
      content = content.replace(/`(.+?)`/g, '<code>$1</code>')
      result.push(`<li>${content}</li>`)
      continue
    }
    
    // Обычный текст
    if (inOrderedList) { result.push('</ol>'); inOrderedList = false }
    if (inUnorderedList) { result.push('</ul>'); inUnorderedList = false }
    
    if (!inParagraph) {
      result.push('<p>')
      inParagraph = true
    } else {
      result.push('<br>')
    }
    
    // Обрабатываем форматирование
    let content = line
    content = content.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    content = content.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')
    content = content.replace(/`(.+?)`/g, '<code>$1</code>')
    result.push(content)
  }
  
  // Закрываем открытые теги
  if (inParagraph) result.push('</p>')
  if (inOrderedList) result.push('</ol>')
  if (inUnorderedList) result.push('</ul>')
  
  return result.join('')
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
  sources?: Array<{
    content: string
    page?: number
    source_type?: string
    similarity?: number
  }>
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

      // Используем answer если есть, иначе response
      const answerText = response.answer || response.response || ''

      const assistantMessage: Message = {
        role: 'assistant',
        content: answerText,
        timestamp: new Date().toISOString(),
        sources: response.sources || []
      }

      setMessages(prev => [...prev, assistantMessage])

      // Если тикет уже создан (ticketCreated из ответа)
      if (response.ticketCreated && !ticketCreated) {
        setTicketCreated(true)
      }

      // Если нужно создать тикет (старый формат для совместимости)
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
            <div 
              className="message-content"
              dangerouslySetInnerHTML={{
                __html: formatMarkdown(message.content)
              }}
            />
            {message.sources && message.sources.length > 0 && (
              <div className="message-sources">
                <div className="sources-label">Источники:</div>
                <div className="sources-list">
                  {message.sources.slice(0, 3).map((source, sIdx) => (
                    <div key={sIdx} className="source-item">
                      {source.page && <span>Страница {source.page}</span>}
                      {source.similarity && (
                        <span className="similarity">
                          Релевантность: {(source.similarity * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
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
          style={{ color: 'white', background: 'linear-gradient(135deg, #0066CC 0%, #00A651 100%)' }}
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

