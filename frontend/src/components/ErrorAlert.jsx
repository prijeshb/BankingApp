/**
 * Inline error box for form-level errors.
 * Use aria-describedby on the form/field to link it to this element.
 */
export default function ErrorAlert({ message, id }) {
  if (!message) return null
  return (
    <div
      id={id}
      role="alert"
      className="rounded-md bg-red-50 border border-red-300 px-4 py-3 text-sm text-red-700"
    >
      {message}
    </div>
  )
}
