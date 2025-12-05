import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTickets } from '../hooks/useTickets'
import { useTranslation } from 'react-i18next'
import TicketCard from '../components/TicketCard'
import { LogOut, RefreshCw, FileText, User } from 'lucide-react'
import LanguageSwitcher from '../components/LanguageSwitcher'

export default function DepartmentDashboard() {
  const { user, userProfile, signOut } = useAuth()
  const navigate = useNavigate()
  const { t } = useTranslation()

  // Фильтруем тикеты по department_id пользователя
  // Инженеры видят только тикеты своего департамента
  const { data: tickets = [], isLoading: loading, refetch: refetchTickets, error: ticketsError } = useTickets({
    department_id: userProfile?.department_id,
    status: 'in_progress' // Показываем только тикеты в работе
  })

  const loadTickets = () => {
    refetchTickets()
  }

  const handleLogout = async () => {
    await signOut()
    navigate('/login')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-cyan-50 to-green-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-gray-700 font-medium">{t('common.loading')}</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-50 to-green-50">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{t('dashboard.departmentTickets')}</h1>
              {userProfile?.department_id && (
                <p className="text-sm text-gray-500 mt-1">
                  Показываются только тикеты вашего департамента
                </p>
              )}
            </div>
            <div className="flex items-center gap-4">
              <LanguageSwitcher />
              <div className="flex items-center gap-2 text-gray-700">
                <User className="w-4 h-4" />
                <span className="text-sm font-medium">{userProfile?.name || user?.email}</span>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <LogOut className="w-4 h-4" />
                {t('auth.logout')}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <section>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-900">{t('dashboard.myTickets')}</h2>
            <button
              onClick={loadTickets}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              {t('dashboard.refresh')}
            </button>
          </div>
          
          {ticketsError ? (
            <div className="bg-red-50 border border-red-200 rounded-xl shadow-sm p-12 text-center">
              <FileText className="w-16 h-16 text-red-400 mx-auto mb-4" />
              <p className="text-lg font-medium text-red-900 mb-2">Ошибка загрузки тикетов</p>
              <p className="text-sm text-red-600">
                {ticketsError.message || 'Не удалось загрузить тикеты'}
              </p>
            </div>
          ) : tickets.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-12 text-center">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-900 mb-2">{t('dashboard.noTickets')}</p>
              <p className="text-sm text-gray-500">
                Нет тикетов в работе для вашего департамента
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {tickets.map((ticket) => (
                <TicketCard
                  key={ticket.id}
                  ticket={ticket}
                  onClick={() => navigate(`/tickets/${ticket.id}`)}
                />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
