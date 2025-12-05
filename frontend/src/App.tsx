import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import AdminDashboard from './pages/AdminDashboard'
import DepartmentDashboard from './pages/DepartmentDashboard'
import EngineerDashboard from './pages/EngineerDashboard'
import CallAgentDashboard from './pages/CallAgentDashboard'
import TicketDetail from './pages/TicketDetail'
import PublicSupport from './pages/PublicSupport'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/support" element={<PublicSupport />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['admin', 'supervisor']}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/department"
            element={
              <ProtectedRoute allowedRoles={['department_user', 'operator']}>
                <DepartmentDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/engineer"
            element={
              <ProtectedRoute allowedRoles={['engineer']}>
                <EngineerDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/call-agent"
            element={
              <ProtectedRoute allowedRoles={['call_agent']}>
                <CallAgentDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/tickets/:id"
            element={
              <ProtectedRoute>
                <TicketDetail />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/support" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App

