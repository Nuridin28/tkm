import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { useTranslation } from 'react-i18next'
import { Clock, Zap, MessageCircle, Phone, Mail, Globe, User } from 'lucide-react'

interface TicketCardProps {
  ticket: any
  onClick: () => void
}

export default function TicketCard({ ticket, onClick }: TicketCardProps) {
  const { t } = useTranslation()

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'border-l-red-500 bg-red-50'
      case 'high':
        return 'border-l-orange-500 bg-orange-50'
      case 'medium':
        return 'border-l-blue-500 bg-blue-50'
      case 'low':
        return 'border-l-gray-400 bg-gray-50'
      default:
        return 'border-l-gray-300 bg-white'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'new':
        return 'bg-blue-100 text-blue-800'
      case 'accepted':
        return 'bg-yellow-100 text-yellow-800'
      case 'in_progress':
        return 'bg-blue-100 text-blue-800'
      case 'resolved':
      case 'auto_resolved':
        return 'bg-green-100 text-green-800'
      case 'closed':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'telegram':
        return <MessageCircle className="w-3 h-3" />
      case 'whatsapp':
        return <Phone className="w-3 h-3" />
      case 'email':
        return <Mail className="w-3 h-3" />
      case 'portal':
      case 'chat':
        return <Globe className="w-3 h-3" />
      case 'phone':
      case 'call_agent':
        return <Phone className="w-3 h-3" />
      default:
        return <User className="w-3 h-3" />
    }
  }

  const getSourceLabel = (source: string) => {
    return t(`tickets.source.${source}`, source)
  }

  return (
    <div
      className={`${getPriorityColor(ticket.priority)} bg-white rounded-xl p-4 shadow-md hover:shadow-lg transition-all duration-300 cursor-pointer border-l-4 h-full flex flex-col`}
      onClick={onClick}
    >
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-mono">#{ticket.id.slice(0, 8)}</span>
          {ticket.source && (
            <span className="flex items-center gap-1 text-xs text-gray-600" title={getSourceLabel(ticket.source)}>
              {getSourceIcon(ticket.source)}
              <span className="hidden sm:inline">{getSourceLabel(ticket.source)}</span>
            </span>
          )}
        </div>
        <span className={`px-2 py-1 rounded text-xs font-medium uppercase ${getStatusColor(ticket.status)}`}>
          {t(`tickets.${ticket.status}`, ticket.status)}
        </span>
      </div>

      <h3 className="text-gray-900 font-semibold text-lg mb-2 line-clamp-2 flex-grow">
        {ticket.subject}
      </h3>

      {(ticket.category || ticket.subcategory) && (
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          {ticket.category && (
            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
              {ticket.category}
            </span>
          )}
          {ticket.subcategory && (
            <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium">
              {ticket.subcategory}
            </span>
          )}
        </div>
      )}

      <p className="text-gray-600 text-sm mb-4 line-clamp-2 flex-grow">
        {ticket.description.slice(0, 100)}...
      </p>

      <div className="flex justify-between items-center mt-auto pt-2 border-t border-gray-200">
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Clock className="w-3 h-3" />
          <span>{format(new Date(ticket.created_at), 'dd MMM yyyy HH:mm', { locale: ru })}</span>
        </div>
        {ticket.auto_resolved && (
          <span className="flex items-center gap-1 bg-green-100 text-green-800 px-2 py-1 rounded text-xs font-medium">
            <Zap className="w-3 h-3" />
            {t('tickets.auto')}
          </span>
        )}
      </div>
    </div>
  )
}

