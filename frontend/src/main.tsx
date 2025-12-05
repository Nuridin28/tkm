import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import App from './App'
import './index.css'
import './i18n/config'

// Настройка React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000, // 30 секунд по умолчанию
      gcTime: 5 * 60 * 1000, // 5 минут в кэше
      refetchOnWindowFocus: false, // Не обновлять при фокусе окна
      refetchOnMount: false, // Не обновлять если данные свежие
      retry: 1, // Повторить только 1 раз при ошибке
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </React.StrictMode>,
)

