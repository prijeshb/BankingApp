import { createContext, useContext, useState, useCallback } from 'react'

const ToastContext = createContext(null)

let _id = 0

const STYLES = {
  success: 'bg-green-50 border-green-400 text-green-800',
  error:   'bg-red-50   border-red-400   text-red-800',
  warning: 'bg-yellow-50 border-yellow-400 text-yellow-800',
  info:    'bg-blue-50  border-blue-400  text-blue-800',
}

const ICONS = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' }

// ── Toast item ────────────────────────────────────────────────────────────────
function ToastItem({ toast, onDismiss }) {
  const style = STYLES[toast.type] ?? STYLES.info
  const icon  = ICONS[toast.type]  ?? ICONS.info

  return (
    <div
      role={toast.type === 'error' ? 'alert' : 'status'}
      className={`flex items-start gap-3 border rounded-lg p-3 shadow-md ${style}`}
    >
      <span aria-hidden="true" className="text-lg leading-none shrink-0">{icon}</span>
      <span className="flex-1 text-sm">{toast.message}</span>
      <button
        type="button"
        aria-label="Dismiss notification"
        className="text-current opacity-60 hover:opacity-100 focus:outline-none focus:ring-1 focus:ring-current rounded"
        onClick={() => onDismiss(toast.id)}
      >
        ×
      </button>
    </div>
  )
}

// ── Toast stack (fixed overlay) ───────────────────────────────────────────────
function ToastStack({ toasts, onDismiss }) {
  if (!toasts.length) return null
  return (
    <div
      className="fixed top-4 right-4 z-50 flex flex-col gap-2 w-80"
      aria-live="polite"
      aria-label="Notifications"
    >
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>
  )
}

// ── Provider ──────────────────────────────────────────────────────────────────
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((message, type = 'info') => {
    const id = ++_id
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000)
  }, [])

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <ToastStack toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  )
}

export const useToast = () => {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used inside ToastProvider')
  return ctx
}
