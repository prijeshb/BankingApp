import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { listAccounts, createAccount, deleteAccount } from '../api/accounts'
import { canDeleteAccount } from '../utils/permissions'
import { useToast } from '../context/ToastContext'
import Badge      from '../components/Badge'
import Spinner    from '../components/Spinner'
import ErrorAlert from '../components/ErrorAlert'

// ── Helpers ───────────────────────────────────────────────────────────────────

const fmt = (n) =>
  parseFloat(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

// ── Dashboard page ────────────────────────────────────────────────────────────

export default function Dashboard() {
  const [accounts,   setAccounts]   = useState([])
  const [loading,    setLoading]    = useState(true)
  const [showModal,  setShowModal]  = useState(false)
  const navigate  = useNavigate()
  const { addToast } = useToast()
  const headingRef = useRef(null)

  useEffect(() => { headingRef.current?.focus() }, [])

  const load = useCallback(async () => {
    try {
      const { data } = await listAccounts()
      setAccounts(data.accounts)
    } catch {
      addToast('Failed to load accounts', 'error')
    } finally {
      setLoading(false)
    }
  }, [addToast])

  useEffect(() => { load() }, [load])

  const [confirmDeleteId, setConfirmDeleteId] = useState(null)

  const handleDelete = (acct) => {
    setConfirmDeleteId(acct.id)
  }

  const handleConfirmDelete = async (acct) => {
    setConfirmDeleteId(null)
    try {
      await deleteAccount(acct.id)
      addToast('Account closed', 'success')
      load()
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Cannot close account'
      addToast(msg, 'error')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1
          ref={headingRef}
          tabIndex={-1}
          className="text-xl font-bold text-gray-900 outline-none"
        >
          My Accounts
        </h1>
        <button
          type="button"
          onClick={() => setShowModal(true)}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          + New Account
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-16" aria-busy="true"><Spinner /></div>
      ) : accounts.length === 0 ? (
        <div className="rounded-xl border-2 border-dashed border-gray-200 bg-white py-20 text-center">
          <p className="text-gray-400 text-lg font-medium">No accounts yet</p>
          <p className="text-gray-400 text-sm mt-1">Click <strong>+ New Account</strong> to get started</p>
        </div>
      ) : (
        <ul
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          aria-label="Your bank accounts"
        >
          {accounts.map((acct) => (
            <AccountCard
              key={acct.id}
              account={acct}
              onOpen={() => navigate(`/accounts/${acct.id}`)}
              onDelete={() => handleDelete(acct)}
              confirmingDelete={confirmDeleteId === acct.id}
              onConfirmDelete={() => handleConfirmDelete(acct)}
              onCancelDelete={() => setConfirmDeleteId(null)}
            />
          ))}
        </ul>
      )}

      {showModal && (
        <NewAccountModal
          onClose={() => setShowModal(false)}
          onCreated={() => { setShowModal(false); load() }}
        />
      )}
    </div>
  )
}

// ── Account card ──────────────────────────────────────────────────────────────

function AccountCard({ account, onOpen, onDelete, confirmingDelete, onConfirmDelete, onCancelDelete }) {
  const deletable = canDeleteAccount(account)

  return (
    <li className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-3 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-xs text-gray-400 font-mono truncate">{account.account_number}</p>
          <div className="mt-1 flex items-center gap-2">
            <Badge value={account.account_type} />
            {!account.is_active && <Badge value="INACTIVE" label="INACTIVE" />}
          </div>
        </div>
        <span className="text-xs font-medium text-gray-500 shrink-0">{account.currency}</span>
      </div>

      <p className="text-2xl font-bold text-gray-900">{fmt(account.balance)}</p>

      {confirmingDelete ? (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 space-y-2">
          <p className="text-xs font-medium text-red-800">Close this account? This cannot be undone.</p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onConfirmDelete}
              className="flex-1 rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              Yes, close
            </button>
            <button
              type="button"
              onClick={onCancelDelete}
              className="flex-1 rounded-md bg-white border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="flex gap-2 pt-1">
          <button
            type="button"
            onClick={onOpen}
            className="flex-1 rounded-md bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            View
          </button>
          <button
            type="button"
            onClick={onDelete}
            disabled={!deletable}
            aria-disabled={!deletable}
            title={!deletable ? 'Balance must be zero to close this account' : 'Close account'}
            className="rounded-md px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-red-400"
          >
            Close
          </button>
        </div>
      )}
    </li>
  )
}

// ── New account modal ─────────────────────────────────────────────────────────

function NewAccountModal({ onClose, onCreated }) {
  const [type,     setType]     = useState('CHECKING')
  const [currency, setCurrency] = useState('USD')
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState('')
  const { addToast } = useToast()
  const firstRef   = useRef(null)

  // Focus first field & allow Escape to close
  useEffect(() => {
    firstRef.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await createAccount(type, currency)
      addToast('Account opened successfully', 'success')
      onCreated()
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not create account')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 px-4"
    >
      <div className="w-full max-w-sm bg-white rounded-xl shadow-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 id="modal-title" className="text-lg font-semibold text-gray-900">Open New Account</h2>
          <button
            type="button"
            aria-label="Close dialog"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <ErrorAlert message={error} />

          <div>
            <label htmlFor="acct-type" className="block text-sm font-medium text-gray-700">
              Account type <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <select
              id="acct-type"
              ref={firstRef}
              value={type}
              onChange={(e) => setType(e.target.value)}
              aria-required="true"
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="CHECKING">Checking</option>
              <option value="SAVINGS">Savings</option>
            </select>
          </div>

          <div>
            <label htmlFor="acct-currency" className="block text-sm font-medium text-gray-700">
              Currency <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <select
              id="acct-currency"
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              aria-required="true"
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="USD">USD – US Dollar</option>
              <option value="EUR">EUR – Euro</option>
              <option value="GBP">GBP – British Pound</option>
            </select>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-md border border-gray-300 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 rounded-md bg-blue-600 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {loading && <Spinner />}
              {loading ? 'Opening…' : 'Open account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
