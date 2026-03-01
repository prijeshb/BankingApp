import { FEATURES } from '../config/features'

/**
 * Returns true if the named feature flag is enabled.
 * Usage: const cardsEnabled = useFeature('CARDS')
 */
export const useFeature = (flag) => Boolean(FEATURES[flag])
