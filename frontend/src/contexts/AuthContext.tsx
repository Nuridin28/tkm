import React, { createContext, useContext, useEffect, useState } from 'react'
import { createClient, SupabaseClient, User } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY || ''

if (!supabaseUrl || !supabaseKey || supabaseUrl.includes('your-project') || supabaseKey.includes('your-anon')) {
  const errorMsg = `
❌ Supabase environment variables are missing or not configured!

Please create a .env file in the frontend directory with your Supabase credentials:

VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_KEY=your-anon-key
VITE_API_URL=http://localhost:8000

Steps:
1. Create frontend/.env file
2. Add your Supabase URL and keys from Supabase Dashboard > Settings > API
3. Restart the dev server (npm run dev)
`
  console.error(errorMsg)

  if (typeof window !== 'undefined') {
    alert('Supabase configuration missing!\n\nPlease check console for details and create .env file.')
  }
}

let supabase: SupabaseClient

try {
  supabase = createClient(supabaseUrl, supabaseKey)
} catch (error) {
  console.error('Failed to create Supabase client:', error)
  supabase = createClient('https://placeholder.supabase.co', 'placeholder-key')
}

interface UserProfile {
  id: string
  email: string
  name: string
  role: string
  department_id?: string
}

interface AuthContextType {
  user: User | null
  userProfile: UserProfile | null
  supabase: SupabaseClient
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const lastProfileIdRef = React.useRef<string | null>(null)
  const lastProfileRoleRef = React.useRef<string | null>(null)
  const profileCacheRef = React.useRef<UserProfile | null>(null)

  const loadUserProfile = async (userId: string) => {
    try {
      console.log('🔍 Loading user profile for:', userId)

      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout after 5 seconds')), 5000)
      )

      console.log('🔍 Executing query for user ID:', userId)
      const queryPromise = supabase
        .from('users')
        .select('id, email, name, role, department_id')
        .eq('id', userId)
        .single()

      console.log('🔍 Query promise created, waiting for response...')

      console.log('⏳ Waiting for query response (5s timeout)...')

      let result: any
      try {
        result = await Promise.race([queryPromise, timeoutPromise])
      } catch (timeoutError: any) {
        if (timeoutError.message?.includes('timeout')) {
          console.error('⏱️ Query timed out! This usually means:')
          console.error('1. RLS policy is blocking the request')
          console.error('2. User profile does not exist in public.users')
          console.error('3. Network/connection issue')
          console.error('')
          console.error('💡 Solution: Create user profile in public.users table')
          console.error('Run this SQL in Supabase SQL Editor:')
          console.error(`
INSERT INTO public.users (id, email, name, role, created_at, updated_at)
SELECT
    id,
    email,
    'Пользователь' as name,
    'admin' as role,
    NOW(),
    NOW()
FROM auth.users
WHERE id = '${userId}'
ON CONFLICT (id) DO UPDATE
SET updated_at = NOW();
          `)
          return null
        }
        throw timeoutError
      }

      const { data, error } = result || {}

      console.log('🔍 Query completed!')
      console.log('🔍 Query result:', {
        hasData: !!data,
        hasError: !!error,
        data: data ? { id: data.id, email: data.email, role: data.role, name: data.name } : null,
        errorCode: error?.code,
        errorMessage: error?.message,
        fullData: data,
        fullError: error
      })

      if (data) {
        console.log('🔍 RAW DATA FROM SUPABASE QUERY:')
        console.log('🔍 Full data object:', data)
        console.log('🔍 Raw role from DB:', data.role)
        console.log('🔍 Role type:', typeof data.role)
        console.log('🔍 Role value (stringified):', JSON.stringify(data.role))
        console.log('🔍 Full profile data:', JSON.stringify(data, null, 2))

        if (data.role !== 'admin' && data.role !== 'department_user') {
          console.warn('⚠️ Unexpected role value:', data.role)
        }
      }

      if (error) {
        console.error('❌ Error loading user profile:', error)
        console.error('Error code:', error.code)
        console.error('Error message:', error.message)
        console.error('Error details:', error.details)
        console.error('Error hint:', error.hint)

        if (error.code === 'PGRST116') {
          console.error('⚠️ User profile NOT FOUND in public.users table!')
          console.error('📝 Run this SQL in Supabase SQL Editor:')
          console.error(`
INSERT INTO public.users (id, email, name, role, created_at, updated_at)
SELECT
    id,
    email,
    'Пользователь',
    'admin',
    NOW(),
    NOW()
FROM auth.users
WHERE id = '${userId}'
ON CONFLICT (id) DO UPDATE
SET updated_at = NOW();
          `)
        } else if (error.code === '42501') {
          console.error('⚠️ Permission denied! Check RLS policies.')
          console.error('Make sure RLS policy "Users can view own profile" is enabled.')
        }

        return null
      }

      if (!data) {
        console.warn('⚠️ No profile data returned for user:', userId)
        console.warn('This might be an RLS policy issue or the user does not exist in public.users')
        return null
      }

      console.log('✅ User profile loaded successfully from DB')
      console.log('✅ Raw data from DB:', JSON.stringify(data, null, 2))
      console.log('✅ Role from DB:', data.role, 'Type:', typeof data.role)

      const profile: UserProfile = {
        id: data.id,
        email: data.email,
        name: data.name,
        role: String(data.role).trim(),
        department_id: data.department_id
      }

      console.log('✅ Final profile object:', profile)
      console.log('✅ Profile role:', profile.role)
      return profile
    } catch (error: any) {
      console.error('❌ Exception loading user profile:', error)
      console.error('Exception type:', error?.constructor?.name)
      console.error('Exception message:', error?.message)
      console.error('Exception stack:', error?.stack)
      return null
    }
  }

  useEffect(() => {
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      setUser(session?.user ?? null)

      if (session?.user) {
        const profile = await loadUserProfile(session.user.id)
        if (!profile && session.user) {
          console.warn('⚠️ Profile not found in public.users, using auth user data as fallback')
          const fallbackRole = session.user.user_metadata?.role || 'department_user'
          console.warn('⚠️ Fallback role:', fallbackRole, 'from user_metadata:', session.user.user_metadata)
          setUserProfile({
            id: session.user.id,
            email: session.user.email || '',
            name: session.user.user_metadata?.name || session.user.email || 'Пользователь',
            role: fallbackRole
          })
        } else {
          console.log('✅ Profile loaded successfully, role:', profile?.role)
          setUserProfile(profile)
        }
      } else {
        setUserProfile(null)
      }

      setLoading(false)
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log('🔔 Auth state changed:', event, 'User:', session?.user?.id)

      const userId = session?.user?.id

      if (userId === lastProfileIdRef.current && profileCacheRef.current &&
          (event === 'TOKEN_REFRESHED' || event === 'SIGNED_IN')) {
        console.log(`⏭️ Skipping profile reload for ${event} (same user, profile cached)`)
        setUser(session?.user ?? null)
        return
      }

      setUser(session?.user ?? null)

      if (session?.user && userId) {
        if (userId !== lastProfileIdRef.current) {
          console.log('🔄 User changed, clearing cache')
          lastProfileIdRef.current = userId
          lastProfileRoleRef.current = null
          profileCacheRef.current = null
        }

        if (profileCacheRef.current && profileCacheRef.current.id === userId) {
          console.log('✅ Using cached profile, skipping DB query')
          setUserProfile(profileCacheRef.current)
          return
        }

        console.log('📥 Loading profile from DB...')
        const profile = await loadUserProfile(userId)

        if (!profile && session.user) {
          console.warn('⚠️ Profile not found in public.users, using auth user data as fallback')
          const fallbackRole = session.user.user_metadata?.role || 'department_user'
          console.warn('⚠️ Fallback role:', fallbackRole, 'from user_metadata:', session.user.user_metadata)

          const fallbackProfile: UserProfile = {
            id: session.user.id,
            email: session.user.email || '',
            name: session.user.user_metadata?.name || session.user.email || 'Пользователь',
            role: fallbackRole
          }

          if (lastProfileRoleRef.current !== fallbackRole) {
            console.log('✅ Setting fallback profile')
            lastProfileRoleRef.current = fallbackRole
            profileCacheRef.current = fallbackProfile
            setUserProfile(fallbackProfile)
          } else {
            console.log('⏭️ Fallback profile unchanged, skipping update')
          }
        } else if (profile) {
          if (lastProfileRoleRef.current !== profile.role) {
            console.log('✅ Profile loaded successfully, role:', profile.role)
            lastProfileRoleRef.current = profile.role
            profileCacheRef.current = profile
            setUserProfile(profile)
          } else {
            console.log('⏭️ Profile role unchanged, skipping update')
            profileCacheRef.current = profile
          }
        }
      } else {
        console.log('🚪 User signed out, clearing cache')
        lastProfileIdRef.current = null
        lastProfileRoleRef.current = null
        profileCacheRef.current = null
        setUserProfile(null)
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  const signIn = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (error) throw error

    if (data.user) {
      setUser(data.user)
      console.log('🔍 Sign in successful, loading profile for:', data.user.id, data.user.email)
      const profile = await loadUserProfile(data.user.id)

      if (!profile && data.user) {
        console.error('❌ Profile NOT found in public.users table!')
        console.error('❌ User ID:', data.user.id)
        console.error('❌ Email:', data.user.email)
        console.error('')
        console.error('📝 SOLUTION: Run this SQL in Supabase SQL Editor:')
        console.error(`
INSERT INTO public.users (id, email, name, role, created_at, updated_at)
SELECT
    id,
    email,
    'Администратор' as name,
    'admin' as role,
    NOW(),
    NOW()
FROM auth.users
WHERE id = '${data.user.id}'
ON CONFLICT (id) DO UPDATE
SET role = 'admin', updated_at = NOW();
        `)
        console.warn('⚠️ Using fallback profile with role: department_user')
        console.warn('⚠️ This is temporary - create profile in public.users for correct role!')
        setUserProfile({
          id: data.user.id,
          email: data.user.email || '',
          name: data.user.user_metadata?.name || data.user.email || 'Пользователь',
          role: 'department_user'
        })
      } else {
        console.log('✅ Profile loaded successfully from public.users')
        console.log('✅ Role:', profile?.role)
        setUserProfile(profile)
      }
    }
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  }

  return (
    <AuthContext.Provider value={{ user, userProfile, supabase, signIn, signOut, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

