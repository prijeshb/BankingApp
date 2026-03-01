import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ToastProvider } from './context/ToastContext'
import { AuthProvider }  from './context/AuthContext'
import { FEATURES }      from './config/features'

import ProtectedRoute from './components/ProtectedRoute'
import Layout         from './components/Layout'

import Login        from './pages/Login'
import Register     from './pages/Register'
import Dashboard    from './pages/Dashboard'
import AccountDetail from './pages/AccountDetail'
import TransferForm  from './pages/TransferForm'
import StatementPage from './pages/StatementPage'

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/login"    element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected routes — ProtectedRoute renders Outlet or redirects */}
            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
                <Route index                    element={<Dashboard />} />
                <Route path="accounts/:id"      element={<AccountDetail />} />

                {FEATURES.TRANSFERS && (
                  <Route path="transfer" element={<TransferForm />} />
                )}
                {FEATURES.STATEMENTS && (
                  <Route path="accounts/:id/statements" element={<StatementPage />} />
                )}
              </Route>
            </Route>

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  )
}
