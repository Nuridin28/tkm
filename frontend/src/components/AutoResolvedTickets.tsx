import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { getAutoResolvedTickets } from '../services/api'
import { Zap, MessageSquare, Clock, TrendingUp, User } from 'lucide-react'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

interface AutoResolvedTicket {
  id: string
  type: string
  subject: string
  description: string
  ai_response: string
  category?: string
  department?: string
  priority: string
  status: string
  auto_resolved: boolean
  confidence: number
  max_similarity: number
  client_type?: string
  language: string
  response_time_ms: number
  created_at: string
  user_id?: string
  session_id?: string
  sources?: Array<{
    content: string
    page?: number
    source_type?: string
    similarity?: number
  }>
}

export default function AutoResolvedTickets() {
  const { t } = useTranslation()
  const [tickets, setTickets] = useState<AutoResolvedTicket[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  useEffect(() => {
    loadTickets()
    const interval = setInterval(loadTickets, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadTickets = async () => {
    try {
      setLoading(true)
      const data = await getAutoResolvedTickets({ limit: 100 })
      console.log('Auto-resolved tickets loaded:', data.length, data)
      setTickets(data || [])
    } catch (error) {
      console.error('Error loading auto-resolved tickets:', error)
      setTickets([])
    } finally {
      setLoading(false)
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'text-red-600 bg-red-50'
      case 'high':
        return 'text-orange-600 bg-orange-50'
      case 'medium':
        return 'text-blue-600 bg-blue-50'
      case 'low':
        return 'text-gray-600 bg-gray-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  if (loading && tickets.length === 0) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Авторешенные тикеты</h2>
          <p className="text-sm text-gray-500 mt-1">
            Тикеты, которые были решены автоматически ИИ без создания тикета
          </p>
        </div>
        <button
          onClick={loadTickets}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Обновить
        </button>
      </div>

      {tickets.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <Zap className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">Нет авторешенных тикетов</p>
          <p className="text-sm text-gray-500">
            Авторешенные тикеты появятся здесь, когда ИИ ответит на вопросы пользователей без создания тикета
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {tickets.map((ticket) => (
            <div
              key={ticket.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Zap className="w-5 h-5 text-green-600" />
                      <span className="text-xs font-mono text-gray-500">#{ticket.id.slice(0, 8)}</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(ticket.priority)}`}>
                        {ticket.priority}
                      </span>
                      {ticket.category && (
                        <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-700">
                          {ticket.category}
                        </span>
                      )}
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{ticket.subject}</h3>
                    <p className="text-sm text-gray-600 mb-3">{ticket.description}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
                  <div className="flex items-center gap-2 text-gray-600">
                    <TrendingUp className="w-4 h-4" />
                    <span>Уверенность: {(ticket.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-600">
                    <Clock className="w-4 h-4" />
                    <span>{(ticket.response_time_ms / 1000).toFixed(1)}с</span>
                  </div>
                  {ticket.client_type && (
                    <div className="flex items-center gap-2 text-gray-600">
                      <User className="w-4 h-4" />
                      <span>{ticket.client_type === 'corporate' ? 'Корпоративный' : 'Частный'}</span>
                    </div>
                  )}
                  <div className="text-gray-600">
                    {format(new Date(ticket.created_at), 'dd MMM yyyy HH:mm', { locale: ru })}
                  </div>
                </div>

                <button
                  onClick={() => setExpandedId(expandedId === ticket.id ? null : ticket.id)}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  {expandedId === ticket.id ? 'Скрыть детали' : 'Показать детали'}
                </button>

                {expandedId === ticket.id && (
                  <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                        <MessageSquare className="w-4 h-4" />
                        Ответ ИИ:
                      </h4>
                      <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap">
                        {ticket.ai_response}
                      </div>
                    </div>

                    {ticket.sources && ticket.sources.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">Источники:</h4>
                        <div className="space-y-2">
                          {ticket.sources.slice(0, 3).map((source, idx) => (
                            <div key={idx} className="bg-blue-50 rounded-lg p-3 text-xs">
                              <div className="flex justify-between items-center mb-1">
                                <span className="font-medium">
                                  {source.source_type || 'Документ'} {source.page && `(Стр. ${source.page})`}
                                </span>
                                {source.similarity && (
                                  <span className="text-gray-600">
                                    Релевантность: {(source.similarity * 100).toFixed(0)}%
                                  </span>
                                )}
                              </div>
                              <p className="text-gray-700 line-clamp-2">{source.content}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

