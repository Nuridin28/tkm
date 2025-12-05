import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles?: string[]
}

export default function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user, userProfile, loading } = useAuth()

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Загрузка...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && userProfile) {
    const userRole = userProfile.role
    if (!allowedRoles.includes(userRole)) {
      // Redirect to dashboard which will redirect based on role
      return <Navigate to="/dashboard" replace />
    }
  }

  // If profile not loaded yet but user exists, wait a bit
  if (!userProfile && user) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Загрузка профиля...</div>
  }

  return <>{children}</>
}

