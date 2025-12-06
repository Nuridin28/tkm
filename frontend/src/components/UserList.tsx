import { useState } from 'react'
import { useUsers, useDeleteUser } from '../hooks/useUsers'
import { useAuth } from '../contexts/AuthContext'
import { useTranslation } from 'react-i18next'
import RegisterUser from '../pages/RegisterUser'
import { Users, Plus, Trash2, Loader2 } from 'lucide-react'

export default function UserList() {
  const [showRegister, setShowRegister] = useState(false)
  const [error, setError] = useState('')
  const [deletingUserId, setDeletingUserId] = useState<string | null>(null)
  const { userProfile } = useAuth()
  const { t } = useTranslation()

  const { data: users = [], isLoading: loading } = useUsers()
  const deleteUserMutation = useDeleteUser()

  const getRoleBadgeColor = (role: string) => {
    const colors: Record<string, string> = {
      admin: 'bg-red-100 text-red-800',
      supervisor: 'bg-orange-100 text-orange-800',
      department_user: 'bg-blue-100 text-blue-800',
      operator: 'bg-blue-100 text-blue-800',
      engineer: 'bg-green-100 text-green-800',
      call_agent: 'bg-cyan-100 text-cyan-800'
    }
    return colors[role] || 'bg-gray-100 text-gray-800'
  }

  const handleDelete = async (userId: string, userName: string) => {
    if (!confirm(t('users.deleteConfirm', { name: userName }))) {
      return
    }

    setDeletingUserId(userId)
    setError('')

    try {
      await deleteUserMutation.mutateAsync(userId)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || t('common.error')
      setError(errorMessage)
    } finally {
      setDeletingUserId(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">{t('users.title')}</h2>
        <button
          onClick={() => setShowRegister(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          {t('users.addUser')}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-4">
          {error}
        </div>
      )}

      {users.length === 0 ? (
        <div className="text-center py-12">
          <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">{t('users.noUsers')}</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('users.name')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('users.email')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('users.role')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('users.department')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('users.createdAt')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{user.name}</td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">{user.email}</td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRoleBadgeColor(user.role)}`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">{user.department_name || user.department_id || '-'}</td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.created_at ? new Date(user.created_at).toLocaleDateString('ru-RU') : '-'}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm">
                    {user.id !== userProfile?.id ? (
                      <button
                        onClick={() => handleDelete(user.id, user.name)}
                        disabled={deletingUserId === user.id}
                        className="text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed"
                        title={t('common.delete')}
                      >
                        {deletingUserId === user.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                    ) : (
                      <span className="text-gray-400 text-xs italic">{t('common.you') || 'Вы'}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showRegister && (
        <RegisterUser
          onClose={() => setShowRegister(false)}
          onSuccess={() => {
            setShowRegister(false)
          }}
        />
      )}
    </div>
  )
}
