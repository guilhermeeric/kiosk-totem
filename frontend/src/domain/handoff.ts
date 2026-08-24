/** QR handoff URL construction — shared by the totem (start QR, handoff overlay). */

export function buildHandoffUrl(input: { origin: string; sessionId: string }): string {
  const { origin, sessionId } = input
  return `${origin}/handoff/${sessionId}`
}

/** Order tracking URL — the phone opens this after scanning the receipt QR. */
export function buildTrackUrl(input: { origin: string; orderId: number }): string {
  const { origin, orderId } = input
  return `${origin}/track/${orderId}`
}

/** QR image URL for arbitrary content (rendered by the backend /qr endpoint). */
export function buildQrUrl(content: string): string {
  return `/qr?content=${encodeURIComponent(content)}`
}

export type HandoffMode = 'invalid' | 'adopt'

/** Which state the handoff view should render, given the URL params. */
export function handoffMode(sessionId: string): HandoffMode {
  if (!sessionId.trim()) return 'invalid'
  return 'adopt'
}
