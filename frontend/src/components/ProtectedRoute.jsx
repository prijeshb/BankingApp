import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Spinner from './Spinner'

/**
 * Route guard for authenticated pages.
 * - Shows a full-page spinner while the silent-login check runs on mount.
 * - Redirects to /login when no access token is present.
 * - Renders <Outlet /> (nested routes) for authenticated users.
 */
export default function ProtectedRoute() {
  const { accessToken, loading } = useAuth()
  if (loading)       return <Spinner fullPage />
  if (!accessToken)  return <Navigate to="/login" replace />
  return <Outlet />
}
