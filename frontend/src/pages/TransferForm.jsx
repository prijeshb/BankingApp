import { useState, useEffect } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { v4 as uuidv4 } from 'uuid'
import * as accountsApi from '../api/accounts'
import * as transfersApi from '../api/transfers'
import { canTransferFrom } from '../utils/permissions'
import { useToast } from '../context/ToastContext'
import Spinner from '../components/Spinner'
import ErrorAlert from '../components/ErrorAlert'

export default function TransferForm() {
  const navigate  = useNavigate()
  const location  = useLocation()
  const { addToast } = useToast()

  // If navigated here from an account page, we have a back target
  const fromAccountId = location.state?.fromAccountId
  const backTo = fromAccountId ? `/accounts/${fromAccountId}` : '/'

  const [accounts,       setAccounts]       = useState([])
  const [loadingAccts,   setLoadingAccts]   = useState(true)
  const [submitting,     setSubmitting]     = useState(false)
  const [error,          setError]          = useState(null)
  const [fieldErrors,    setFieldErrors]    = useState({})
  const [idempotencyKey, setIdempotencyKey] = useState(uuidv4())

  const [form, setForm] = useState({
    from_account_id: '',
    to_account_id:   '',
    amount:          '',
    description:     '',
  })

  // ── Load user's accounts ───────────────────────────────────────────────────
  useEffect(() => {
    accountsApi.listAccounts()
      .then(({ data }) => {
        const eligible = (data.accounts ?? []).filter(canTransferFrom)
        setAccounts(eligible)
        if (eligible.length > 0) {
          const preselect = fromAccountId && eligible.find(a => a.id === fromAccountId)
            ? fromAccountId
            : eligible[0].id
          setForm(f => ({ ...f, from_account_id: preselect }))
        }
      })
      .catch(() => setError('Could not load your accounts.'))
      .finally(() => setLoadingAccts(false))
  }, [])

  // ── Field helpers ──────────────────────────────────────────────────────────
  function handleChange(e) {
    const { name, value } = e.target
    setForm(f => ({ ...f, [name]: value }))
    if (fieldErrors[name]) {
      setFieldErrors(fe => ({ ...fe, [name]: null }))
    }
  }

  function validate() {
    const errs = {}
    if (!form.from_account_id) errs.from_account_id = 'Select a source account.'
    if (!form.to_account_id.trim()) {
      errs.to_account_id = 'Recipient account number is required.'
    }
    if (!form.amount) {
      errs.amount = 'Amount is required.'
    } else if (isNaN(form.amount) || parseFloat(form.amount) <= 0) {
      errs.amount = 'Amount must be a positive number.'
    }
    return errs
  }

  // ── Submit ─────────────────────────────────────────────────────────────────
  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setFieldErrors({})

    const errs = validate()
    if (Object.keys(errs).length > 0) {
      setFieldErrors(errs)
      // Focus first error field
      const firstKey = Object.keys(errs)[0]
      document.getElementById(`tf-${firstKey}`)?.focus()
      return
    }

    setSubmitting(true)
    try {
      // Resolve account number to UUID
      const recipient = form.to_account_id.trim()
      let toAccountId = recipient

      // If it's not already a UUID, look it up by account number
      const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(recipient)
      if (!isUUID) {
        try {
          const { data } = await accountsApi.lookupByNumber(recipient)
          toAccountId = data.id
        } catch {
          setFieldErrors({ to_account_id: 'Account not found. Check the number and try again.' })
          setSubmitting(false)
          return
        }
      }

      const payload = {
        from_account_id: form.from_account_id,
        to_account_id:   toAccountId,
        amount:          parseFloat(form.amount).toFixed(2),
        idempotency_key: idempotencyKey,
        ...(form.description.trim() && { description: form.description.trim() }),
      }
      await transfersApi.createTransfer(payload)
      addToast(`Transfer of $${parseFloat(form.amount).toFixed(2)} completed`, 'success')
      navigate(backTo)
    } catch (err) {
      const status = err.response?.status
      const detail = err.response?.data?.detail

      if (status === 409) {
        addToast('This transfer was already processed', 'info')
        navigate(backTo)
        return
      }

      if (status === 422 && Array.isArray(detail)) {
        const fe = {}
        for (const item of detail) {
          const field = item.loc?.[item.loc.length - 1]
          if (field) fe[field] = item.msg
        }
        setFieldErrors(fe)
        return
      }

      const msg = typeof detail === 'string' ? detail : 'Something went wrong — please try again.'
      setError(msg)
      addToast(msg, 'error')
      // Regenerate idempotency key so user can retry
      setIdempotencyKey(uuidv4())
    } finally {
      setSubmitting(false)
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  if (loadingAccts) return <Spinner fullPage />

  const selectedAccount = accounts.find(a => a.id === form.from_account_id)

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6" tabIndex="-1" id="transfer-heading">
        New Transfer
      </h1>

      {accounts.length === 0 && (
        <div
          role="alert"
          className="mb-6 rounded-lg bg-yellow-50 border border-yellow-200 p-4 text-yellow-800"
        >
          <p className="font-medium">No eligible accounts</p>
          <p className="text-sm mt-1">
            You need at least one active account to make a transfer.{' '}
            <Link to="/" className="underline hover:no-underline focus:outline-none focus:ring-2 focus:ring-yellow-600 rounded">
              Go to Dashboard
            </Link>
          </p>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        noValidate
        aria-labelledby="transfer-heading"
        className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5"
      >
        {error && <ErrorAlert message={error} />}

        {/* From account */}
        <div>
          <label
            htmlFor="tf-from_account_id"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            From account <span aria-hidden="true" className="text-red-500">*</span>
          </label>
          <select
            id="tf-from_account_id"
            name="from_account_id"
            value={form.from_account_id}
            onChange={handleChange}
            disabled={accounts.length === 0 || submitting}
            aria-required="true"
            aria-describedby={fieldErrors.from_account_id ? 'tf-from_account_id-err' : undefined}
            className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400 ${
              fieldErrors.from_account_id ? 'border-red-400 bg-red-50' : 'border-gray-300'
            }`}
          >
            {accounts.length === 0 ? (
              <option value="">No active accounts available</option>
            ) : (
              accounts.map(acct => (
                <option key={acct.id} value={acct.id}>
                  {acct.account_number} — {acct.account_type} (
                  {acct.currency} {parseFloat(acct.balance).toFixed(2)})
                </option>
              ))
            )}
          </select>
          {fieldErrors.from_account_id && (
            <p id="tf-from_account_id-err" role="alert" className="mt-1 text-xs text-red-600">
              {fieldErrors.from_account_id}
            </p>
          )}
          {selectedAccount && (
            <p className="mt-1 text-xs text-gray-500">
              Available balance:{' '}
              <span className="font-medium">
                {selectedAccount.currency} {parseFloat(selectedAccount.balance).toFixed(2)}
              </span>
            </p>
          )}
        </div>

        {/* To account */}
        <div>
          <label
            htmlFor="tf-to_account_id"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Recipient account number <span aria-hidden="true" className="text-red-500">*</span>
          </label>
          <input
            id="tf-to_account_id"
            name="to_account_id"
            type="text"
            value={form.to_account_id}
            onChange={handleChange}
            disabled={submitting}
            placeholder="e.g. ACC9739133631"
            autoComplete="off"
            spellCheck="false"
            aria-required="true"
            aria-describedby={
              fieldErrors.to_account_id ? 'tf-to_account_id-err' : 'tf-to_account_id-hint'
            }
            className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 ${
              fieldErrors.to_account_id ? 'border-red-400 bg-red-50' : 'border-gray-300'
            }`}
          />
          {fieldErrors.to_account_id ? (
            <p id="tf-to_account_id-err" role="alert" className="mt-1 text-xs text-red-600">
              {fieldErrors.to_account_id}
            </p>
          ) : (
            <p id="tf-to_account_id-hint" className="mt-1 text-xs text-gray-500">
              Ask the recipient to share their account number from their dashboard.
            </p>
          )}
        </div>

        {/* Amount */}
        <div>
          <label
            htmlFor="tf-amount"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Amount <span aria-hidden="true" className="text-red-500">*</span>
          </label>
          <div className="relative">
            <span
              className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500 text-sm"
              aria-hidden="true"
            >
              {selectedAccount?.currency ?? '$'}
            </span>
            <input
              id="tf-amount"
              name="amount"
              type="number"
              min="0.01"
              step="0.01"
              value={form.amount}
              onChange={handleChange}
              disabled={submitting}
              placeholder="0.00"
              aria-required="true"
              aria-describedby={fieldErrors.amount ? 'tf-amount-err' : undefined}
              className={`w-full rounded-lg border pl-14 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 ${
                fieldErrors.amount ? 'border-red-400 bg-red-50' : 'border-gray-300'
              }`}
            />
          </div>
          {fieldErrors.amount && (
            <p id="tf-amount-err" role="alert" className="mt-1 text-xs text-red-600">
              {fieldErrors.amount}
            </p>
          )}
        </div>

        {/* Description (optional) */}
        <div>
          <label
            htmlFor="tf-description"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Description{' '}
            <span className="text-gray-400 font-normal">(optional)</span>
          </label>
          <input
            id="tf-description"
            name="description"
            type="text"
            maxLength={255}
            value={form.description}
            onChange={handleChange}
            disabled={submitting}
            placeholder="e.g. Rent payment"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
          />
        </div>


        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={submitting || accounts.length === 0}
            aria-label={submitting ? 'Submitting transfer…' : undefined}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {submitting && (
              <svg
                className="h-4 w-4 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
            )}
            {submitting ? 'Sending…' : 'Send Transfer'}
          </button>
          <Link
            to={backTo}
            className="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-400 transition-colors"
          >
            {fromAccountId ? '← Back' : 'Cancel'}
          </Link>
        </div>
      </form>
    </div>
  )
}
