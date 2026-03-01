/**
 * Feature flags — driven by VITE_FEATURE_* env vars.
 * Each flag defaults ON unless explicitly set to the string 'false'.
 * Toggle in .env.local without any code changes.
 */
export const FEATURES = {
  CARDS:         import.meta.env.VITE_FEATURE_CARDS         !== 'false',
  STATEMENTS:    import.meta.env.VITE_FEATURE_STATEMENTS    !== 'false',
  TRANSFERS:     import.meta.env.VITE_FEATURE_TRANSFERS     !== 'false',
  VIRTUAL_CARDS: import.meta.env.VITE_FEATURE_VIRTUAL_CARDS !== 'false',
}
