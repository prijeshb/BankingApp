/**
 * Resource-state permission helpers.
 * All "can I do X to this resource?" logic lives here so every component
 * uses the same rules — no scattered inline checks.
 */

// ── Account permissions ───────────────────────────────────────────────────────

/** Account can be closed only when active AND balance is exactly zero. */
export const canDeleteAccount = (acct) =>
  acct.is_active && parseFloat(acct.balance) === 0

/** Cards can only be issued against an active account. */
export const canIssueCard = (acct) => acct.is_active

/** Only active accounts appear in the transfer "from" dropdown. */
export const canTransferFrom = (acct) => acct.is_active

// ── Card permissions ──────────────────────────────────────────────────────────

/** Block is available only on ACTIVE cards. */
export const canBlockCard = (card) => card.status === 'ACTIVE'

/** Unblock is available only on BLOCKED cards. */
export const canUnblockCard = (card) => card.status === 'BLOCKED'

/** Status can never be changed on an EXPIRED card. */
export const canChangeCardStatus = (card) => card.status !== 'EXPIRED'

/** EXPIRED cards are read-only — they cannot be deleted via the UI. */
export const canDeleteCard = (card) => card.status !== 'EXPIRED'
