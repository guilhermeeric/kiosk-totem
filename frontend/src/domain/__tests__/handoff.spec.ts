import { describe, expect, it } from 'vitest'

import { buildHandoffUrl, buildQrUrl, handoffMode } from '../handoff'

describe('handoffMode', () => {
  it('is invalid when the session id is missing or empty', () => {
    expect(handoffMode('')).toBe('invalid')
    expect(handoffMode('   ')).toBe('invalid')
  })

  it('adopts whenever a session is present — there is no name stage anymore', () => {
    expect(handoffMode('abc-123')).toBe('adopt')
  })
})

describe('buildHandoffUrl', () => {
  it('builds the handoff URL from origin and session id only (no name in QR)', () => {
    expect(buildHandoffUrl({ origin: 'http://192.168.1.50:5173', sessionId: 'abc-123' })).toBe(
      'http://192.168.1.50:5173/handoff/abc-123',
    )
  })
})

describe('buildQrUrl', () => {
  it('encodes arbitrary content into the qr endpoint', () => {
    expect(buildQrUrl('http://x/handoff/s1')).toBe(
      '/qr?content=http%3A%2F%2Fx%2Fhandoff%2Fs1',
    )
  })
})
