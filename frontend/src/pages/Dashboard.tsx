import { useEffect, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Dashboard() {
  const { user, userProfile, loading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const redirectAttemptedRef = useRef(false)
  const lastRoleRef = useRef<string | null>(null)

  useEffect(() => {
    console.log('Dashboard useEffect:', { 
      loading, 
      user: !!user, 
      userProfile: !!userProfile, 
      role: userProfile?.role,
      redirectAttempted: redirectAttemptedRef.current,
      currentPath: location.pathname
    })
    
    if (loading) {
      console.log('Still loading auth...')
      return
    }
    
    if (!user) {
      console.log('No user, redirecting to login')
      navigate('/login', { replace: true })
      return
    }

    // Если уже не на странице /dashboard, не делаем редирект
    if (location.pathname !== '/dashboard') {
      console.log('Already redirected, current path:', location.pathname)
      return
    }

    // Если редирект уже был выполнен, не делаем его снова
    if (redirectAttemptedRef.current) {
      console.log('Redirect already attempted, skipping')
      return
    }

    // If no profile after 3 seconds, redirect anyway (fallback)
    if (!userProfile) {
      console.log('User exists but no profile yet, waiting...')
      const timer = setTimeout(() => {
        if (!redirectAttemptedRef.current && location.pathname === '/dashboard') {
          console.log('⚠️ Profile not loaded after timeout, redirecting to department as fallback')
          redirectAttemptedRef.current = true
          navigate('/department', { replace: true })
        }
      }, 3000)
      return () => clearTimeout(timer)
    }

    const role = userProfile.role
    const normalizedRole = role?.toLowerCase()?.trim()
    
    // Если роль не изменилась и редирект уже был, не делаем его снова
    if (lastRoleRef.current === normalizedRole && redirectAttemptedRef.current) {
      console.log('Role unchanged and redirect already attempted, skipping')
      return
    }

    console.log('✅ User profile:', userProfile)
    console.log('✅ Redirecting based on role:', role, 'Type:', typeof role)
    console.log('✅ Normalized role:', normalizedRole)
    
    // Сохраняем роль и помечаем редирект как выполненный
    lastRoleRef.current = normalizedRole
    redirectAttemptedRef.current = true
    
    // Redirect based on role
    if (normalizedRole === 'admin' || normalizedRole === 'supervisor') {
      console.log('→ Redirecting to /admin (admin/supervisor)')
      navigate('/admin', { replace: true })
    } else if (normalizedRole === 'engineer') {
      console.log('→ Redirecting to /engineer')
      navigate('/engineer', { replace: true })
    } else if (normalizedRole === 'call_agent') {
      console.log('→ Redirecting to /call-agent')
      navigate('/call-agent', { replace: true })
    } else if (normalizedRole === 'department_user' || normalizedRole === 'operator') {
      console.log('→ Redirecting to /department (department_user/operator)')
      navigate('/department', { replace: true })
    } else {
      console.warn('⚠️ Unknown role:', normalizedRole, 'Full profile:', userProfile)
      console.warn('⚠️ Default redirect to /department')
      navigate('/department', { replace: true })
    }
  }, [userProfile, user, loading, navigate, location.pathname])

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div>Загрузка...</div>
        <div style={{ fontSize: '0.875rem', color: '#666', marginTop: '1rem' }}>
          Проверка авторизации...
        </div>
      </div>
    )
  }

  if (!user) {
    return null // Will redirect to login
  }

  if (!userProfile) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div>Загрузка профиля...</div>
        <div style={{ fontSize: '0.875rem', color: '#666', marginTop: '1rem' }}>
          Если это занимает слишком долго, проверьте консоль браузера (F12)
        </div>
        <div style={{ fontSize: '0.75rem', color: '#999', marginTop: '0.5rem' }}>
          Возможно, нужно создать профиль в базе данных
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: '2rem', textAlign: 'center', color: 'white' }}>
      <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>Перенаправление...</div>
      <div style={{ fontSize: '1rem', marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}>
        <div>Роль: <strong>{userProfile.role}</strong></div>
        <div style={{ fontSize: '0.875rem', marginTop: '0.5rem', opacity: 0.9 }}>
          Email: {userProfile.email}
        </div>
        <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', opacity: 0.7 }}>
          Проверьте консоль браузера (F12) для деталей
        </div>
      </div>
    </div>
  )
}

