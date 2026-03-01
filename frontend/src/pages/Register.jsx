import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth }  from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import ErrorAlert   from '../components/ErrorAlert'
import Spinner      from '../components/Spinner'

const FIELDS = [
  { id: 'full_name', label: 'Full name',              type: 'text',     ac: 'name' },
  { id: 'email',     label: 'Email',                   type: 'email',    ac: 'email' },
  { id: 'password',  label: 'Password (min 8 chars)',  type: 'password', ac: 'new-password' },
]

export default function Register() {
  const { register } = useAuth()
  const { addToast } = useToast()
  const navigate     = useNavigate()

  const [form,    setForm]    = useState({ full_name: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form.email, form.password, form.full_name)
      addToast('Account created — please sign in', 'success')
      navigate('/login')
    } catch (err) {
      const msg =
        err.response?.data?.error?.message ||
        err.response?.data?.detail?.[0]?.msg ||
        'Registration failed — please try again'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Create your account</h1>
          <p className="mt-2 text-sm text-gray-500">
            Already have an account?{' '}
            <Link
              to="/login"
              className="text-blue-600 hover:underline focus:outline-none focus:ring-1 focus:ring-blue-500 rounded"
            >
              Sign in
            </Link>
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-xl shadow p-6 space-y-4"
          noValidate
          aria-describedby={error ? 'reg-error' : undefined}
        >
          <ErrorAlert message={error} id="reg-error" />

          {FIELDS.map(({ id, label, type, ac }) => (
            <div key={id}>
              <label htmlFor={id} className="block text-sm font-medium text-gray-700">
                {label} <span aria-hidden="true" className="text-red-500">*</span>
              </label>
              <input
                id={id}
                type={type}
                value={form[id]}
                onChange={set(id)}
                required
                aria-required="true"
                autoComplete={ac}
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          ))}

          <button
            type="submit"
            disabled={loading}
            aria-label={loading ? 'Creating account, please wait' : 'Create account'}
            className="w-full flex items-center justify-center gap-2 rounded-md bg-blue-600 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
          >
            {loading && <Spinner />}
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>
      </div>
    </div>
  )
}
