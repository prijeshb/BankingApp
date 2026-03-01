export default function Spinner({ fullPage = false }) {
  const el = (
    <div
      role="status"
      aria-label="Loading"
      className="inline-block h-5 w-5 animate-spin rounded-full border-[3px] border-blue-600 border-t-transparent"
    />
  )
  if (fullPage) {
    return (
      <div className="flex h-screen items-center justify-center">{el}</div>
    )
  }
  return el
}
