import { useTranslation } from 'react-i18next'
import { Ticket, Zap, CheckCircle2 } from 'lucide-react'

interface MetricsCardsProps {
  metrics: {
    total_tickets: number
    auto_resolve_rate: number
    sla_compliance: number
  }
}

export default function MetricsCards({ metrics }: MetricsCardsProps) {
  const { t } = useTranslation()

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div className="bg-white rounded-xl shadow-sm p-6 border-l-4 border-blue-500">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">{t('admin.totalTickets')}</p>
            <p className="text-3xl font-bold text-gray-900">{metrics.total_tickets}</p>
          </div>
          <div className="bg-blue-100 rounded-full p-3">
            <Ticket className="w-6 h-6 text-blue-600" />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6 border-l-4 border-green-500">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">{t('admin.autoResolveRate')}</p>
            <p className="text-3xl font-bold text-gray-900">{metrics.auto_resolve_rate.toFixed(1)}%</p>
          </div>
          <div className="bg-green-100 rounded-full p-3">
            <Zap className="w-6 h-6 text-green-600" />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6 border-l-4 border-green-500">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">{t('admin.slaCompliance')}</p>
            <p className="text-3xl font-bold text-gray-900">{metrics.sla_compliance.toFixed(1)}%</p>
          </div>
          <div className="bg-green-100 rounded-full p-3">
            <CheckCircle2 className="w-6 h-6 text-green-600" />
          </div>
        </div>
      </div>
    </div>
  )
}
