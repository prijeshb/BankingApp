const STYLES = {
  // Card / account status
  ACTIVE:        'bg-green-100 text-green-800',
  BLOCKED:       'bg-yellow-100 text-yellow-800',
  EXPIRED:       'bg-gray-100 text-gray-600',
  // Account types
  CHECKING:      'bg-blue-100 text-blue-800',
  SAVINGS:       'bg-purple-100 text-purple-800',
  // Card types
  DEBIT:         'bg-indigo-100 text-indigo-800',
  VIRTUAL:       'bg-cyan-100 text-cyan-800',
  // Transfer / transaction status
  COMPLETED:     'bg-green-100 text-green-800',
  PENDING:       'bg-yellow-100 text-yellow-800',
  FAILED:        'bg-red-100 text-red-800',
  TRANSFER_OUT:  'bg-red-100 text-red-700',
  TRANSFER_IN:   'bg-green-100 text-green-700',
  CREDIT:        'bg-green-100 text-green-700',
  DEBIT_TXN:     'bg-red-100 text-red-700',
}

/**
 * Colored status pill. Always includes a text label so status is never
 * conveyed by color alone (WCAG 1.4.1).
 */
export default function Badge({ value, label }) {
  const style = STYLES[value] ?? 'bg-gray-100 text-gray-700'
  const display = label ?? value
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}
      aria-label={`Status: ${display}`}
    >
      {display}
    </span>
  )
}
