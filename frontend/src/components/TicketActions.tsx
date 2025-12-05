import { useState } from 'react'
import { useDeleteTicket, useAssignTicket } from '../hooks/useTickets'
import { useTranslation } from 'react-i18next'
import { Pin, Trash2, X, Building, User, Loader2, Save } from 'lucide-react'

interface TicketActionsProps {
  ticket: any
  onUpdate: () => void
  departments?: any[]
  users?: any[]
}

export default function TicketActions({ ticket, onUpdate, departments = [], users = [] }: TicketActionsProps) {
  const { t } = useTranslation()
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [assignData, setAssignData] = useState({
    assigned_to: ticket.assigned_to || '',
    department_id: ticket.department_id || ''
  })
  const [error, setError] = useState('')

  const deleteTicketMutation = useDeleteTicket()
  const assignTicketMutation = useAssignTicket()

  const handleDelete = async () => {
    setError('')
    try {
      await deleteTicketMutation.mutateAsync(ticket.id)
      setShowDeleteConfirm(false)
      onUpdate()
    } catch (err: any) {
      setError(err.response?.data?.detail || t('common.error'))
    }
  }

  const handleAssign = async () => {
    setError('')
    try {
      await assignTicketMutation.mutateAsync({ ticketId: ticket.id, data: assignData })
      setShowAssignModal(false)
      onUpdate()
    } catch (err: any) {
      setError(err.response?.data?.detail || t('common.error'))
    }
  }

  const loading = deleteTicketMutation.isPending || assignTicketMutation.isPending

  // Скрываем кнопку назначения, если тикет уже подтвержден (статус in_progress)
  // Тикет автоматически назначается в отдел при подтверждении классификации
  const canAssign = ticket.status === 'new' || ticket.status === 'accepted'

  return (
    <div className="flex gap-2">
      {canAssign && (
        <button
          onClick={() => setShowAssignModal(true)}
          className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
          title={t('tickets.assign')}
        >
          <Pin className="w-4 h-4" />
          {t('tickets.assign')}
        </button>
      )}
      <button
        onClick={() => setShowDeleteConfirm(true)}
        className="flex items-center gap-2 px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors"
        title={t('tickets.delete')}
      >
        <Trash2 className="w-4 h-4" />
        {t('tickets.delete')}
      </button>

      {showAssignModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowAssignModal(false)}>
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">{t('tickets.assign')}</h3>
              <button onClick={() => setShowAssignModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-4">
                {error}
              </div>
            )}
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Building className="w-4 h-4 inline mr-1" />
                  {t('tickets.department')}
                </label>
                <select
                  value={assignData.department_id}
                  onChange={(e) => setAssignData({ ...assignData, department_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                >
                  <option value="">{t('tickets.department')}</option>
                  {departments.map((dept) => (
                    <option key={dept.id} value={dept.id}>{dept.name}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <User className="w-4 h-4 inline mr-1" />
                  {t('tickets.assigned')}
                </label>
                <select
                  value={assignData.assigned_to}
                  onChange={(e) => setAssignData({ ...assignData, assigned_to: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                >
                  <option value="">{t('tickets.assigned')}</option>
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>{user.name} ({user.email})</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowAssignModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleAssign}
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                {loading ? t('common.loading') : t('common.save')}
              </button>
            </div>
          </div>
        </div>
      )}

      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowDeleteConfirm(false)}>
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">{t('tickets.delete')}?</h3>
              <button onClick={() => setShowDeleteConfirm(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <p className="text-gray-700 mb-2">
              {t('tickets.delete')} "{ticket.subject}"?
            </p>
            <p className="text-sm text-red-600 mb-4">{t('common.error')}</p>
            
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-4">
                {error}
              </div>
            )}
            
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleDelete}
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                {loading ? t('common.loading') : t('tickets.delete')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
