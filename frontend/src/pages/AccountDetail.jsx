import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getAccount, deposit as depositApi, withdraw as withdrawApi } from '../api/accounts'
import { listTransactions }                  from '../api/transactions'
import { listCards, issueCard, updateCardStatus, deleteCard, revealCard } from '../api/cards'
import {
  canIssueCard,
  canBlockCard,
  canUnblockCard,
  canDeleteCard,
} from '../utils/permissions'
import { useToast }   from '../context/ToastContext'
import { FEATURES }   from '../config/features'
import FeatureGate    from '../components/FeatureGate'
import Badge          from '../components/Badge'
import Spinner        from '../components/Spinner'
import ErrorAlert     from '../components/ErrorAlert'

const fmt = (n) =>
  parseFloat(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const TAB_TRANSACTIONS = 'transactions'
const TAB_CARDS        = 'cards'

// ── AccountDetail page ────────────────────────────────────────────────────────

export default function AccountDetail() {
  const { id }       = useParams()
  const { addToast } = useToast()

  const [account,      setAccount]      = useState(null)
  const [loading,      setLoading]      = useState(true)
  const [tab,          setTab]          = useState(TAB_TRANSACTIONS)
  const [showDeposit,   setShowDeposit]   = useState(false)
  const [showWithdraw,  setShowWithdraw]  = useState(false)
  const [refreshKey,    setRefreshKey]    = useState(0)

  const loadAccount = useCallback(async () => {
    try {
      const { data } = await getAccount(id)
      setAccount(data)
    } catch {
      addToast('Could not load account', 'error')
    } finally {
      setLoading(false)
    }
  }, [id, addToast])

  useEffect(() => { loadAccount() }, [loadAccount])

  if (loading) return <div className="flex justify-center py-16" aria-busy="true"><Spinner /></div>
  if (!account) return <p className="text-gray-500 text-center py-16">Account not found.</p>

  const tabs = [
    { id: TAB_TRANSACTIONS, label: 'Transactions' },
    ...(FEATURES.CARDS ? [{ id: TAB_CARDS, label: 'Cards' }] : []),
  ]

  return (
    <div className="space-y-6">
      {/* Account header */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link
              to="/"
              className="text-sm text-blue-600 hover:underline focus:outline-none focus:ring-1 focus:ring-blue-500 rounded"
            >
              ← Accounts
            </Link>
            <h1 className="mt-1 text-xl font-bold text-gray-900">{account.account_number}</h1>
            <div className="mt-1 flex items-center gap-2">
              <Badge value={account.account_type} />
              <span className="text-xs text-gray-400">{account.currency}</span>
              {!account.is_active && <Badge value="INACTIVE" label="INACTIVE" />}
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-400 uppercase tracking-wide">Balance</p>
            <p className="text-3xl font-bold text-gray-900">{fmt(account.balance)}</p>
          </div>
        </div>

        {/* Action buttons */}
        <div className="mt-4 flex flex-wrap gap-3">
          {account.is_active && (
            <button
              type="button"
              onClick={() => setShowDeposit(true)}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              + Deposit
            </button>
          )}
          {account.is_active && parseFloat(account.balance) > 0 && (
            <button
              type="button"
              onClick={() => setShowWithdraw(true)}
              className="rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-white hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-400"
            >
              − Withdraw
            </button>
          )}
          {FEATURES.TRANSFERS && (
            <Link
              to="/transfer"
              state={{ fromAccountId: account.id }}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Transfer
            </Link>
          )}
        </div>
      </div>

      {/* Deposit modal */}
      {showDeposit && (
        <DepositModal
          account={account}
          onClose={() => setShowDeposit(false)}
          onSuccess={() => { setShowDeposit(false); loadAccount(); setRefreshKey(k => k + 1) }}
        />
      )}

      {/* Withdraw modal */}
      {showWithdraw && (
        <WithdrawalModal
          account={account}
          onClose={() => setShowWithdraw(false)}
          onSuccess={() => { setShowWithdraw(false); loadAccount(); setRefreshKey(k => k + 1) }}
        />
      )}

      {/* Tabs */}
      {tabs.length > 1 && (
        <div role="tablist" aria-label="Account sections" className="flex border-b border-gray-200">
          {tabs.map((t) => (
            <button
              key={t.id}
              role="tab"
              type="button"
              id={`tab-${t.id}`}
              aria-selected={tab === t.id}
              aria-controls={`panel-${t.id}`}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 ${
                tab === t.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      )}

      {/* Tab panels */}
      <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
        {tab === TAB_TRANSACTIONS && <TransactionsTab accountId={id} refreshKey={refreshKey} />}
        <FeatureGate flag="CARDS">
          {tab === TAB_CARDS && <CardsTab account={account} onRefresh={loadAccount} />}
        </FeatureGate>
      </div>
    </div>
  )
}

// ── Deposit modal ──────────────────────────────────────────────────────────────

function DepositModal({ account, onClose, onSuccess }) {
  const [amount,      setAmount]      = useState('')
  const [description, setDescription] = useState('')
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState('')
  const { addToast } = useToast()
  const inputRef = useRef(null)

  useEffect(() => {
    inputRef.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (!amount || parseFloat(amount) <= 0) {
      setError('Enter a valid amount greater than zero.')
      return
    }
    setLoading(true)
    try {
      await depositApi(account.id, parseFloat(amount).toFixed(2), description.trim() || undefined)
      addToast(`Deposited ${account.currency} ${parseFloat(amount).toFixed(2)}`, 'success')
      onSuccess()
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Deposit failed — please try again.'
      setError(msg)
      addToast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="deposit-title"
    >
      <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 id="deposit-title" className="text-lg font-bold text-gray-900">Deposit Funds</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-400 rounded"
          >
            ✕
          </button>
        </div>

        <p className="text-sm text-gray-500">
          Adding funds to <span className="font-medium text-gray-800">{account.account_number}</span>
        </p>

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          {error && <ErrorAlert message={error} />}

          <div>
            <label htmlFor="dep-amount" className="block text-sm font-medium text-gray-700 mb-1">
              Amount <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500 text-sm" aria-hidden="true">
                {account.currency}
              </span>
              <input
                id="dep-amount"
                ref={inputRef}
                type="number"
                min="0.01"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                disabled={loading}
                placeholder="0.00"
                aria-required="true"
                className="w-full rounded-lg border border-gray-300 pl-14 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
              />
            </div>
          </div>

          <div>
            <label htmlFor="dep-desc" className="block text-sm font-medium text-gray-700 mb-1">
              Note <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              id="dep-desc"
              type="text"
              maxLength={255}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={loading}
              placeholder="e.g. Salary"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
            />
          </div>

          <div className="flex gap-3 pt-1">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
            >
              {loading && (
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
              )}
              {loading ? 'Processing…' : 'Deposit'}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400 disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Withdrawal modal ───────────────────────────────────────────────────────────

function WithdrawalModal({ account, onClose, onSuccess }) {
  const [amount,      setAmount]      = useState('')
  const [description, setDescription] = useState('')
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState('')
  const { addToast } = useToast()
  const inputRef = useRef(null)
  const maxBalance = parseFloat(account.balance)

  useEffect(() => {
    inputRef.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    const val = parseFloat(amount)
    if (!amount || val <= 0) {
      setError('Enter a valid amount greater than zero.')
      return
    }
    if (val > maxBalance) {
      setError(`Amount exceeds your available balance of ${account.currency} ${maxBalance.toFixed(2)}.`)
      return
    }
    setLoading(true)
    try {
      await withdrawApi(account.id, val.toFixed(2), description.trim() || undefined)
      addToast(`Withdrew ${account.currency} ${val.toFixed(2)}`, 'success')
      onSuccess()
    } catch (err) {
      const code = err.response?.data?.error?.code
      if (code === 'INSUFFICIENT_FUNDS') {
        setError('Insufficient funds for this withdrawal.')
      } else {
        setError('Withdrawal failed — please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="withdraw-title"
    >
      <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 id="withdraw-title" className="text-lg font-bold text-gray-900">Withdraw Funds</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-400 rounded"
          >
            ✕
          </button>
        </div>

        <p className="text-sm text-gray-500">
          Available balance:{' '}
          <span className="font-medium text-gray-800">
            {account.currency} {maxBalance.toFixed(2)}
          </span>
        </p>

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          {error && <ErrorAlert message={error} />}

          <div>
            <label htmlFor="wd-amount" className="block text-sm font-medium text-gray-700 mb-1">
              Amount <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500 text-sm" aria-hidden="true">
                {account.currency}
              </span>
              <input
                id="wd-amount"
                ref={inputRef}
                type="number"
                min="0.01"
                step="0.01"
                max={maxBalance}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                disabled={loading}
                placeholder="0.00"
                aria-required="true"
                className="w-full rounded-lg border border-gray-300 pl-14 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 disabled:bg-gray-50"
              />
            </div>
          </div>

          <div>
            <label htmlFor="wd-desc" className="block text-sm font-medium text-gray-700 mb-1">
              Note <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              id="wd-desc"
              type="text"
              maxLength={255}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={loading}
              placeholder="e.g. Rent payment"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 disabled:bg-gray-50"
            />
          </div>

          <div className="flex gap-3 pt-1">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-orange-500 px-4 py-2 text-sm font-medium text-white hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-400 disabled:opacity-50"
            >
              {loading && (
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
              )}
              {loading ? 'Processing…' : 'Withdraw'}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400 disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Transactions tab ──────────────────────────────────────────────────────────

function TransactionsTab({ accountId, refreshKey }) {
  const [txns,      setTxns]      = useState([])
  const [loading,   setLoading]   = useState(true)
  const [page,      setPage]      = useState(1)
  const [total,     setTotal]     = useState(0)
  const { addToast } = useToast()
  const LIMIT = 20
  const today      = new Date().toISOString().slice(0, 10)
  const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
  const [startDate, setStartDate] = useState(oneWeekAgo)
  const [endDate,   setEndDate]   = useState(today)
  const [dateErr,   setDateErr]   = useState('')

  const load = useCallback(async (pg = 1) => {
    setDateErr('')
    setLoading(true)
    try {
      const { data } = await listTransactions(accountId, {
        page: pg, limit: LIMIT,
        start_date: startDate || undefined,
        end_date:   endDate   || undefined,
      })
      setTxns(data.transactions)
      setTotal(data.total)
      setPage(pg)
    } catch {
      addToast('Could not load transactions', 'error')
    } finally {
      setLoading(false)
    }
  }, [accountId, startDate, endDate, addToast, refreshKey])

  useEffect(() => { load(1) }, [load])

  const totalPages = Math.ceil(total / LIMIT)

  return (
    <div className="space-y-4">
      {/* Date filter */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          setDateErr('')
          if (startDate && startDate > today) { setDateErr('From date cannot be in the future.'); return }
          if (endDate   && endDate   > today) { setDateErr('To date cannot be in the future.');   return }
          if (startDate && endDate && endDate < startDate) { setDateErr('End date must be on or after start date.'); return }
          load(1)
        }}
        className="bg-white rounded-xl border border-gray-200 p-4 flex flex-wrap items-end gap-3"
        aria-label="Filter transactions by date"
      >
        <div>
          <label htmlFor="tx-start" className="block text-xs font-medium text-gray-600 mb-1">From</label>
          <input
            id="tx-start"
            type="date"
            value={startDate}
            max={today}
            onChange={(e) => setStartDate(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label htmlFor="tx-end" className="block text-xs font-medium text-gray-600 mb-1">To</label>
          <input
            id="tx-end"
            type="date"
            value={endDate}
            max={today}
            onChange={(e) => setEndDate(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <button
            type="submit"
            className="rounded-md bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Filter
          </button>
          {(startDate !== oneWeekAgo || endDate !== today) && (
            <button
              type="button"
              onClick={() => { setStartDate(oneWeekAgo); setEndDate(today); setDateErr('') }}
              className="rounded-md px-3 py-1.5 text-sm font-medium text-red-500 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-400"
            >
              Reset
            </button>
          )}
        </div>
        {dateErr && <p role="alert" className="w-full text-xs text-red-600">{dateErr}</p>}
      </form>

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-12" aria-busy="true"><Spinner /></div>
      ) : txns.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 py-16 text-center text-gray-400">
          No transactions found for this period
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm" aria-label="Transaction history">
              <caption className="sr-only">Transaction history</caption>
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th scope="col" className="px-4 py-3 text-left font-medium text-gray-500">Date</th>
                  <th scope="col" className="px-4 py-3 text-left font-medium text-gray-500">Type</th>
                  <th scope="col" className="px-4 py-3 text-left font-medium text-gray-500">Description</th>
                  <th scope="col" className="px-4 py-3 text-right font-medium text-gray-500">Amount</th>
                  <th scope="col" className="px-4 py-3 text-right font-medium text-gray-500">Balance after</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {txns.map((tx) => (
                  <tr key={tx.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-gray-500">
                      {new Date(tx.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <Badge value={tx.transaction_type} />
                    </td>
                    <td className="px-4 py-3 text-gray-600 max-w-[200px] truncate">
                      {tx.description || '—'}
                    </td>
                    <td className={`px-4 py-3 text-right font-medium whitespace-nowrap ${
                      tx.transaction_type?.includes('IN') || tx.transaction_type === 'DEPOSIT'
                        ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {tx.transaction_type?.includes('IN') || tx.transaction_type === 'DEPOSIT' ? '+' : '−'}
                      {fmt(tx.amount)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600 whitespace-nowrap">
                      {fmt(tx.balance_after)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 text-sm text-gray-600">
              <span>
                Showing {(page - 1) * LIMIT + 1}–{Math.min(page * LIMIT, total)} of {total}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => load(page - 1)}
                  aria-label="Previous page"
                  className="rounded px-3 py-1 border border-gray-300 hover:bg-gray-50 disabled:opacity-40 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  ← Prev
                </button>
                <button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => load(page + 1)}
                  aria-label="Next page"
                  className="rounded px-3 py-1 border border-gray-300 hover:bg-gray-50 disabled:opacity-40 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Cards tab ─────────────────────────────────────────────────────────────────

function CardsTab({ account, onRefresh }) {
  const [cards,               setCards]               = useState([])
  const [loading,             setLoading]             = useState(true)
  const [confirmDeleteCardId, setConfirmDeleteCardId] = useState(null)
  const [revealingCardId,     setRevealingCardId]     = useState(null)   // which card shows pw prompt
  const [revealedData,        setRevealedData]        = useState({})     // cardId → {card_number, cvv, expiry_date}
  const { addToast } = useToast()

  const loadCards = useCallback(async () => {
    try {
      const { data } = await listCards(account.id)
      setCards(data.cards)
    } catch {
      addToast('Could not load cards', 'error')
    } finally {
      setLoading(false)
    }
  }, [account.id, addToast])

  useEffect(() => { loadCards() }, [loadCards])

  // Card limits: max 1 active DEBIT, max 1 active VIRTUAL
  const activeCards  = cards.filter(c => c.status !== 'EXPIRED')
  const hasDebit     = activeCards.some(c => c.card_type === 'DEBIT')
  const hasVirtual   = activeCards.some(c => c.card_type === 'VIRTUAL')

  const handleGenerate = async (cardType) => {
    try {
      await issueCard(account.id, cardType)
      addToast(`${cardType === 'DEBIT' ? 'Debit' : 'Virtual'} card generated`, 'success')
      loadCards()
    } catch (err) {
      addToast(err.response?.data?.error?.message || 'Could not generate card', 'error')
    }
  }

  const handleStatusChange = async (card, newStatus) => {
    try {
      await updateCardStatus(card.id, newStatus)
      addToast(newStatus === 'BLOCKED' ? 'Card blocked' : 'Card activated', 'success')
      loadCards()
    } catch (err) {
      if (err.response?.status === 404) { loadCards(); return }
      addToast('Could not update card status', 'error')
    }
  }

  const handleDelete = (card) => setConfirmDeleteCardId(card.id)

  const handleConfirmDelete = async (card) => {
    setConfirmDeleteCardId(null)
    try {
      await deleteCard(card.id)
      addToast('Card removed', 'success')
      // Clear any revealed data for this card
      setRevealedData(prev => { const n = { ...prev }; delete n[card.id]; return n })
      loadCards()
    } catch (err) {
      if (err.response?.status === 404) { loadCards(); return }
      addToast('Could not remove card', 'error')
    }
  }

  const handleRevealRequest = (card) => setRevealingCardId(card.id)

  const handleRevealSuccess = (cardId, data) => {
    setRevealingCardId(null)
    setRevealedData(prev => ({ ...prev, [cardId]: data }))
  }

  const handleHideDetails = (cardId) => {
    setRevealedData(prev => { const n = { ...prev }; delete n[cardId]; return n })
  }

  return (
    <div className="space-y-5">
      {/* Generate card controls */}
      {canIssueCard(account) && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
          <p className="text-sm font-medium text-gray-700">Generate new card</p>
          <div className="inline-flex items-start gap-2 rounded-lg bg-blue-50 border border-blue-200 px-3 py-2">
            <svg className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clipRule="evenodd" />
            </svg>
            <p className="text-xs text-blue-700">One debit and one virtual card maximum per account.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => handleGenerate('DEBIT')}
              disabled={hasDebit}
              title={hasDebit ? 'You already have a debit card on this account' : undefined}
              aria-disabled={hasDebit}
              className="rounded-md bg-slate-700 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              + Debit card
            </button>
            <FeatureGate flag="VIRTUAL_CARDS">
              <button
                type="button"
                onClick={() => handleGenerate('VIRTUAL')}
                disabled={hasVirtual}
                title={hasVirtual ? 'You already have a virtual card on this account' : undefined}
                aria-disabled={hasVirtual}
                className="rounded-md bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-violet-500 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                + Virtual card
              </button>
            </FeatureGate>
          </div>
        </div>
      )}

      {/* Card list */}
      {loading ? (
        <div className="flex justify-center py-12" aria-busy="true"><Spinner /></div>
      ) : cards.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 py-16 text-center text-gray-400 text-sm">
          No cards on this account yet
        </div>
      ) : (
        <ul className="grid gap-5 sm:grid-cols-2" aria-label="Cards on this account">
          {cards.map((card) => (
            <CardItem
              key={card.id}
              card={card}
              revealed={revealedData[card.id] ?? null}
              confirmingDelete={confirmDeleteCardId === card.id}
              onBlock={() => handleStatusChange(card, 'BLOCKED')}
              onUnblock={() => handleStatusChange(card, 'ACTIVE')}
              onDelete={() => handleDelete(card)}
              onConfirmDelete={() => handleConfirmDelete(card)}
              onCancelDelete={() => setConfirmDeleteCardId(null)}
              onRevealRequest={() => handleRevealRequest(card)}
              onHideDetails={() => handleHideDetails(card.id)}
            />
          ))}
        </ul>
      )}

      {/* Password reveal modal */}
      {revealingCardId && (
        <RevealModal
          cardId={revealingCardId}
          onSuccess={(data) => handleRevealSuccess(revealingCardId, data)}
          onClose={() => setRevealingCardId(null)}
          onCardGone={() => { setRevealingCardId(null); loadCards() }}
        />
      )}
    </div>
  )
}

// ── Card visual (credit-card style) ───────────────────────────────────────────

function CardItem({
  card,
  revealed,
  confirmingDelete,
  onBlock,
  onUnblock,
  onDelete,
  onConfirmDelete,
  onCancelDelete,
  onRevealRequest,
  onHideDetails,
}) {
  const isExpired   = card.status === 'EXPIRED'
  const isBlocked   = card.status === 'BLOCKED'
  const isVirtual   = card.card_type === 'VIRTUAL'
  const deletable   = canDeleteCard(card)
  const blockable   = canBlockCard(card)
  const unblockable = canUnblockCard(card)
  const isRevealed  = !!revealed

  // Gradient based on card type
  const cardGradient = isVirtual
    ? 'from-violet-700 via-indigo-700 to-indigo-800'
    : 'from-slate-800 via-slate-700 to-slate-600'

  const [copied, setCopied] = useState(false)

  // Copy card number to clipboard
  const copyNumber = async () => {
    if (!revealed?.card_number) return
    const plain = revealed.card_number.replace(/\s/g, '')
    try {
      await navigator.clipboard.writeText(plain)
    } catch {
      // Fallback for browsers that block navigator.clipboard
      const el = document.createElement('textarea')
      el.value = plain
      el.style.position = 'fixed'
      el.style.opacity = '0'
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const expiryFormatted = (() => {
    try {
      const d = new Date(card.expiry_date)
      return `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getFullYear()).slice(-2)}`
    } catch { return '—' }
  })()

  return (
    <li className="space-y-3">
      {/* ── Physical card ── */}
      <div
        style={{ perspective: '1000px' }}
        className="w-72"
        aria-label={`${card.card_type} card ending ${card.card_number_masked.slice(-4)}`}
      >
        <div
          style={{
            transformStyle: 'preserve-3d',
            transition: 'transform 0.55s ease',
            transform: isRevealed ? 'rotateY(180deg)' : 'rotateY(0deg)',
            position: 'relative',
            height: '180px',
          }}
        >
          {/* ── FRONT (locked) ── */}
          <div
            style={{ backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden', pointerEvents: isRevealed ? 'none' : 'auto' }}
            className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${cardGradient} p-5 flex flex-col justify-between shadow-lg overflow-hidden`}
          >
            <div className="absolute -top-6 -right-6 w-32 h-32 rounded-full bg-white/5" />
            <div className="absolute -bottom-8 -left-4 w-40 h-40 rounded-full bg-white/5" />

            {/* Top row */}
            <div className="flex items-start justify-between relative z-10">
              <span className="text-white/80 text-xs font-bold tracking-widest uppercase">NexBank</span>
              <span className="text-white/70 text-xs font-medium tracking-wide">{card.card_type}</span>
            </div>

            {/* Chip icon */}
            <div className="relative z-10">
              <svg width="36" height="28" viewBox="0 0 36 28" fill="none" aria-hidden="true">
                <rect x="0" y="0" width="36" height="28" rx="4" fill="#D4AF37" fillOpacity="0.85" />
                <rect x="12" y="0" width="2" height="28" fill="#B8962E" fillOpacity="0.6" />
                <rect x="22" y="0" width="2" height="28" fill="#B8962E" fillOpacity="0.6" />
                <rect x="0" y="10" width="36" height="2" fill="#B8962E" fillOpacity="0.6" />
                <rect x="0" y="16" width="36" height="2" fill="#B8962E" fillOpacity="0.6" />
              </svg>
            </div>

            {/* Masked number + click hint */}
            <div className="relative z-10 space-y-1">
              <p className="font-mono text-white/90 text-sm tracking-widest">
                {card.card_number_masked}
              </p>
              {!isExpired && !isBlocked && (
                <button
                  type="button"
                  onClick={onRevealRequest}
                  className="text-white/60 text-xs hover:text-white/90 focus:outline-none focus:ring-1 focus:ring-white/60 rounded transition-colors"
                >
                  Click to view card details →
                </button>
              )}
              {isBlocked && <p className="text-yellow-300 text-xs font-medium">Card is blocked</p>}
              {isExpired && <p className="text-red-300 text-xs font-medium">Card expired</p>}
            </div>
          </div>

          {/* ── BACK (revealed) ── */}
          <div
            style={{
              backfaceVisibility: 'hidden',
              WebkitBackfaceVisibility: 'hidden',
              transform: 'rotateY(180deg)',
              pointerEvents: isRevealed ? 'auto' : 'none',
            }}
            className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${cardGradient} p-5 flex flex-col justify-between shadow-lg overflow-hidden`}
          >
            <div className="absolute -top-6 -right-6 w-32 h-32 rounded-full bg-white/5" />
            <div className="absolute -bottom-8 -left-4 w-40 h-40 rounded-full bg-white/5" />

            {/* Top row */}
            <div className="flex items-start justify-between relative z-10">
              <span className="text-white/80 text-xs font-bold tracking-widest uppercase">NexBank</span>
              <button
                type="button"
                onClick={onHideDetails}
                className="text-white/60 text-xs hover:text-white/90 focus:outline-none focus:ring-1 focus:ring-white/60 rounded"
                aria-label="Hide card details"
              >
                Hide ✕
              </button>
            </div>

            {/* Full card number + copy */}
            <div className="relative z-10 space-y-1">
              <div className="flex items-center gap-2">
                <p className="font-mono text-white text-sm tracking-widest flex-1">
                  {revealed?.card_number ?? ''}
                </p>
                <button
                  type="button"
                  onClick={copyNumber}
                  aria-label="Copy card number"
                  className="text-white/70 hover:text-white text-xs focus:outline-none focus:ring-1 focus:ring-white/60 rounded px-1 transition-colors"
                >
                  {copied ? 'Copied!' : '⎘ Copy'}
                </button>
              </div>
            </div>

            {/* Expiry + CVV */}
            <div className="relative z-10 flex items-end justify-between">
              <div>
                <p className="text-white/50 text-xs uppercase tracking-wider mb-0.5">Valid thru</p>
                <p className="font-mono text-white text-sm">{revealed?.expiry_date ?? expiryFormatted}</p>
              </div>
              <div>
                <p className="text-white/50 text-xs uppercase tracking-wider mb-0.5">CVV</p>
                <p className="font-mono text-white text-sm">{revealed?.cvv ?? '•••'}</p>
              </div>
              <div>
                <p className="text-white/50 text-xs uppercase tracking-wider mb-0.5">Type</p>
                <p className="text-white/80 text-xs font-medium">{card.card_type}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Card actions (below the card visual) ── */}
      {confirmingDelete ? (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 space-y-2">
          <p className="text-xs font-medium text-red-800">Remove this card?</p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onConfirmDelete}
              className="flex-1 rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              Yes, remove
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
        <div className="flex flex-wrap gap-2">
          {!isExpired && blockable && (
            <button
              type="button"
              onClick={onBlock}
              className="rounded-md bg-yellow-50 border border-yellow-300 px-3 py-1.5 text-xs font-medium text-yellow-700 hover:bg-yellow-100 focus:outline-none focus:ring-2 focus:ring-yellow-400"
            >
              Block
            </button>
          )}
          {!isExpired && unblockable && (
            <button
              type="button"
              onClick={onUnblock}
              className="rounded-md bg-green-50 border border-green-300 px-3 py-1.5 text-xs font-medium text-green-700 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-green-400"
            >
              Unblock
            </button>
          )}
          <button
            type="button"
            onClick={onDelete}
            disabled={!deletable}
            aria-disabled={!deletable}
            title={isExpired ? 'Expired cards cannot be removed' : undefined}
            className="rounded-md bg-red-50 border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-100 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-red-400"
          >
            Remove
          </button>
          {isExpired && (
            <span className="text-xs text-gray-400 italic self-center">Expired</span>
          )}
        </div>
      )}
    </li>
  )
}

// ── Password reveal modal ─────────────────────────────────────────────────────

function RevealModal({ cardId, onSuccess, onClose, onCardGone }) {
  const [password, setPassword] = useState('')
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    inputRef.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (!password) { setError('Please enter your password.'); return }
    setLoading(true)
    try {
      const { data } = await revealCard(cardId, password)
      onSuccess(data)
    } catch (err) {
      const status = err.response?.status
      if (status === 401) {
        setError('Incorrect password. Please try again.')
      } else if (status === 404) {
        onCardGone()
      } else {
        setError('Could not verify — please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="reveal-title"
    >
      <div className="bg-white rounded-xl shadow-xl w-full max-w-xs p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 id="reveal-title" className="text-base font-bold text-gray-900">Verify your identity</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-400 rounded"
          >
            ✕
          </button>
        </div>
        <p className="text-sm text-gray-500">Enter your account password to view full card details.</p>

        <form onSubmit={handleSubmit} noValidate className="space-y-3">
          {error && <p role="alert" className="text-xs text-red-600 bg-red-50 rounded p-2">{error}</p>}
          <div>
            <label htmlFor="reveal-pw" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              id="reveal-pw"
              ref={inputRef}
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError('') }}
              disabled={loading}
              autoComplete="current-password"
              aria-required="true"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
            />
          </div>
          <div className="flex gap-2 pt-1">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading && (
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
              )}
              {loading ? 'Verifying…' : 'View card details'}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400 disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </form>

      </div>
    </div>
  )
}
