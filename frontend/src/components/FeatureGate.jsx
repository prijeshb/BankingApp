import { useFeature } from '../hooks/useFeature'

/**
 * Renders children only when the named feature flag is enabled.
 *
 * Usage:
 *   <FeatureGate flag="CARDS">
 *     <CardsTab />
 *   </FeatureGate>
 *
 * Optional fallback for when the feature is off:
 *   <FeatureGate flag="STATEMENTS" fallback={<p>Statements coming soon</p>}>
 *     <StatementPage />
 *   </FeatureGate>
 */
export default function FeatureGate({ flag, children, fallback = null }) {
  const enabled = useFeature(flag)
  return enabled ? children : fallback
}
