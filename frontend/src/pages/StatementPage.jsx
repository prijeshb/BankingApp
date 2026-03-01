import { useState, useRef, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import * as accountsApi  from '../api/accounts'
import * as statementsApi from '../api/statements'
import { useToast } from '../context/ToastContext'
import Spinner from '../components/Spinner'
import ErrorAlert from '../components/ErrorAlert'
import Badge from '../components/Badge'

// ── Stat card ──────────────────────────────────────────────────────────────
function StatCard({ label, value, accent }) {
  const accentClass = {
    blue:  'bg-blue-50  border-blue-200  text-blue-900',
    green: 'bg-green-50 border-green-200 text-green-900',
    red:   'bg-red-50   border-red-200   text-red-900',
    gray:  'bg-gray-50  border-gray-200  text-gray-900',
  }[accent] ?? 'bg-gray-50 border-gray-200 text-gray-900'

  return (
    <div className={`rounded-xl border p-4 ${accentClass}`}>
      <p className="text-xs font-medium opacity-70 mb-1">{label}</p>
      <p className="text-xl font-bold">{value}</p>
    </div>
  )
}

// ── Transaction type label ─────────────────────────────────────────────────
function TxTypeLabel({ type }) {
  const styles = {
    TRANSFER_IN:  'bg-green-100 text-green-800',
    TRANSFER_OUT: 'bg-red-100   text-red-800',
    DEPOSIT:      'bg-blue-100  text-blue-800',
    WITHDRAWAL:   'bg-orange-100 text-orange-800',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles[type] ?? 'bg-gray-100 text-gray-700'}`}>
      {type?.replace(/_/g, ' ')}
    </span>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────
export default function StatementPage() {
  const { id } = useParams()
  const { addToast } = useToast()

  const [account,    setAccount]    = useState(null)
  const [loadingAcct,setLoadingAcct]= useState(true)

  const today = new Date().toISOString().slice(0, 10)
  const oneMonthAgo = new Date(new Date().setMonth(new Date().getMonth() - 1)).toISOString().slice(0, 10)

  const [startDate, setStartDate] = useState(oneMonthAgo)
  const [endDate,   setEndDate]   = useState(today)
  const [dateError, setDateError] = useState(null)

  const [statement,  setStatement]  = useState(null)
  const [loading,    setLoading]    = useState(false)
  const [error,      setError]      = useState(null)

  const resultsRef = useRef(null)
  const headingRef = useRef(null)

  // focus heading on mount
  useEffect(() => { headingRef.current?.focus() }, [])

  // load account info
  useEffect(() => {
    accountsApi.getAccount(id)
      .then(({ data }) => setAccount(data))
      .catch(() => {
        setError('Could not load account details.')
        addToast('Could not load account details.', 'error')
      })
      .finally(() => setLoadingAcct(false))
  }, [id]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Fetch statement ────────────────────────────────────────────────────────
  async function handleFetch(e) {
    e.preventDefault()
    setDateError(null)
    setError(null)

    if (!startDate || !endDate) {
      setDateError('Both start and end date are required.')
      return
    }
    if (endDate < startDate) {
      setDateError('End date must be on or after start date.')
      return
    }

    setLoading(true)
    setStatement(null)
    try {
      const { data } = await statementsApi.getStatement(id, startDate, endDate)
      setStatement(data)
      // Move focus to results
      setTimeout(() => resultsRef.current?.focus(), 50)
    } catch (err) {
      const detail = err.response?.data?.detail
      const msg = typeof detail === 'string' ? detail : 'Could not load statement — please try again.'
      setError(msg)
      addToast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  // ── Helpers ────────────────────────────────────────────────────────────────
  function fmt(val) {
    return parseFloat(val ?? 0).toFixed(2)
  }

  function fmtDate(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
    })
  }

  function fmtTime(iso) {
    if (!iso) return ''
    return new Date(iso).toLocaleTimeString(undefined, {
      hour: '2-digit', minute: '2-digit',
    })
  }

  // ── Loading state ──────────────────────────────────────────────────────────
  if (loadingAcct) return <Spinner fullPage />

  return (
    <div className="max-w-4xl mx-auto space-y-6">

      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="text-sm text-gray-500">
        <ol className="flex items-center gap-2">
          <li><Link to="/" className="hover:text-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-400 rounded">Dashboard</Link></li>
          <li aria-hidden="true">/</li>
          {account && (
            <>
              <li>
                <Link
                  to={`/accounts/${id}`}
                  className="hover:text-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-400 rounded"
                >
                  {account.account_number}
                </Link>
              </li>
              <li aria-hidden="true">/</li>
            </>
          )}
          <li aria-current="page" className="text-gray-800 font-medium">Statement</li>
        </ol>
      </nav>

      {/* Header */}
      <div>
        <h1
          ref={headingRef}
          tabIndex="-1"
          className="text-2xl font-bold text-gray-900 focus:outline-none"
        >
          Account Statement
        </h1>
        {account && (
          <p className="mt-1 text-sm text-gray-500">
            {account.account_number} &middot;{' '}
            <Badge status={account.account_type} /> &middot;{' '}
            {account.currency}
          </p>
        )}
      </div>

      {/* Date range form */}
      <form
        onSubmit={handleFetch}
        noValidate
        aria-label="Statement date range"
        className="bg-white rounded-xl border border-gray-200 shadow-sm p-5"
      >
        <div className="flex flex-col sm:flex-row gap-4 items-end">
          {/* Start date */}
          <div className="flex-1">
            <label htmlFor="stmt-start" className="block text-sm font-medium text-gray-700 mb-1">
              Start date <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <input
              id="stmt-start"
              type="date"
              value={startDate}
              onChange={e => { setStartDate(e.target.value); setDateError(null) }}
              max={today}
              aria-required="true"
              aria-describedby={dateError ? 'stmt-date-err' : undefined}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                dateError ? 'border-red-400 bg-red-50' : 'border-gray-300'
              }`}
            />
          </div>

          {/* End date */}
          <div className="flex-1">
            <label htmlFor="stmt-end" className="block text-sm font-medium text-gray-700 mb-1">
              End date <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <input
              id="stmt-end"
              type="date"
              value={endDate}
              onChange={e => { setEndDate(e.target.value); setDateError(null) }}
              max={today}
              aria-required="true"
              aria-describedby={dateError ? 'stmt-date-err' : undefined}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                dateError ? 'border-red-400 bg-red-50' : 'border-gray-300'
              }`}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            aria-label={loading ? 'Loading statement…' : undefined}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
          >
            {loading && (
              <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
            )}
            {loading ? 'Loading…' : 'Get Statement'}
          </button>
        </div>

        {dateError && (
          <p id="stmt-date-err" role="alert" className="mt-2 text-xs text-red-600">
            {dateError}
          </p>
        )}
      </form>

      {error && <ErrorAlert message={error} />}

      {/* Results */}
      {loading && (
        <div className="flex justify-center py-12" aria-busy="true" aria-label="Loading statement">
          <Spinner />
        </div>
      )}

      {statement && !loading && (
        <section aria-label="Statement results" ref={resultsRef} tabIndex="-1" className="focus:outline-none space-y-6">

          {/* Period */}
          <p className="text-sm text-gray-500">
            Period:{' '}
            <span className="font-medium text-gray-800">
              {fmtDate(statement.period?.start_date)} – {fmtDate(statement.period?.end_date)}
            </span>
          </p>

          {/* Summary cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" role="list" aria-label="Statement summary">
            <div role="listitem">
              <StatCard
                label="Opening Balance"
                value={`${account?.currency ?? ''} ${fmt(statement.opening_balance)}`}
                accent="gray"
              />
            </div>
            <div role="listitem">
              <StatCard
                label="Closing Balance"
                value={`${account?.currency ?? ''} ${fmt(statement.closing_balance)}`}
                accent="blue"
              />
            </div>
            <div role="listitem">
              <StatCard
                label="Total Credits"
                value={`+ ${fmt(statement.total_credits)}`}
                accent="green"
              />
            </div>
            <div role="listitem">
              <StatCard
                label="Total Debits"
                value={`− ${fmt(statement.total_debits)}`}
                accent="red"
              />
            </div>
          </div>

          {/* Transaction count */}
          <p className="text-sm text-gray-600">
            <span className="font-semibold text-gray-900">{statement.transaction_count}</span>{' '}
            transaction{statement.transaction_count !== 1 ? 's' : ''} in this period.
          </p>

          {/* Transaction table */}
          {statement.transactions?.length > 0 ? (
            <div className="overflow-x-auto rounded-xl border border-gray-200 shadow-sm">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <caption className="sr-only">
                  Transactions from {startDate} to {endDate}
                </caption>
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider text-xs">Date</th>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider text-xs">Type</th>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider text-xs">Description</th>
                    <th scope="col" className="px-4 py-3 text-right font-medium text-gray-500 uppercase tracking-wider text-xs">Amount</th>
                    <th scope="col" className="px-4 py-3 text-right font-medium text-gray-500 uppercase tracking-wider text-xs">Balance After</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                  {statement.transactions.map((tx, idx) => {
                    const isCredit = tx.transaction_type === 'TRANSFER_IN' || tx.transaction_type === 'DEPOSIT'
                    return (
                      <tr key={tx.id ?? idx} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 whitespace-nowrap text-gray-600">
                          <span>{fmtDate(tx.created_at)}</span>
                          <span className="block text-xs text-gray-400">{fmtTime(tx.created_at)}</span>
                        </td>
                        <td className="px-4 py-3">
                          <TxTypeLabel type={tx.transaction_type} />
                        </td>
                        <td className="px-4 py-3 text-gray-700 max-w-xs truncate">
                          {tx.description || <span className="text-gray-400 italic">—</span>}
                        </td>
                        <td className={`px-4 py-3 text-right font-medium tabular-nums whitespace-nowrap ${
                          isCredit ? 'text-green-700' : 'text-red-700'
                        }`}>
                          {isCredit ? '+' : '−'} {fmt(tx.amount)}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-600 tabular-nums whitespace-nowrap">
                          {tx.balance_after != null ? fmt(tx.balance_after) : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="rounded-xl border border-gray-200 bg-gray-50 py-12 text-center text-gray-500">
              <p className="text-sm">No transactions in this period.</p>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
