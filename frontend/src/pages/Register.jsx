import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth }  from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import ErrorAlert   from '../components/ErrorAlert'
import Spinner      from '../components/Spinner'

const FIELDS = [
  { id: 'full_name', label: 'Full name',   type: 'text',     ac: 'name' },
  { id: 'email',     label: 'Email',        type: 'email',    ac: 'email' },
  { id: 'password',  label: 'Password',     type: 'password', ac: 'new-password' },
]

const PW_RULES = [
  { test: (v) => v.length >= 8,        label: 'At least 8 characters' },
  { test: (v) => /[A-Z]/.test(v),      label: 'One uppercase letter' },
  { test: (v) => /[a-z]/.test(v),      label: 'One lowercase letter' },
  { test: (v) => /\d/.test(v),         label: 'One digit' },
  { test: (v) => /[^A-Za-z0-9]/.test(v), label: 'One special character' },
]

export default function Register() {
  const { register } = useAuth()
  const { addToast } = useToast()
  const navigate     = useNavigate()

  const [form,    setForm]    = useState({ full_name: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const passwordValid = PW_RULES.every((r) => r.test(form.password))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!passwordValid) {
      setError('Please fix the password requirements below.')
      return
    }

    setLoading(true)
    try {
      await register(form.email, form.password, form.full_name)
      addToast('Account created — please sign in', 'success')
      navigate('/login')
    } catch (err) {
      const errData = err.response?.data?.error
      const details = errData?.details
      const msg = details?.length
        ? details.map(d => d.message).join('. ')
        : errData?.message || 'Registration failed — please try again'
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
                maxLength={id === 'password' ? 100 : undefined}
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />

              {/* Password strength checklist */}
              {id === 'password' && form.password.length > 0 && (
                <ul className="mt-2 space-y-0.5" aria-label="Password requirements">
                  {PW_RULES.map(({ test, label: ruleLabel }) => {
                    const met = test(form.password)
                    return (
                      <li
                        key={ruleLabel}
                        className={`text-xs flex items-center gap-1.5 ${
                          met ? 'text-green-600' : 'text-gray-400'
                        }`}
                      >
                        <span aria-hidden="true">{met ? '✓' : '○'}</span>
                        <span>{ruleLabel}</span>
                      </li>
                    )
                  })}
                </ul>
              )}
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
