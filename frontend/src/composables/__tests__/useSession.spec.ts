import { beforeEach, describe, expect, it } from 'vitest'

import { useSession } from '../useSession'

beforeEach(() => {
  sessionStorage.clear()
})

describe('useSession', () => {
  it('stores the session id and exposes it', () => {
    const { sessionId, setSession } = useSession()
    setSession('abc-123')
    expect(sessionId.value).toBe('abc-123')
    expect(sessionStorage.getItem('totem.session_id')).toBe('abc-123')
  })

  it('clears the session', () => {
    const { sessionId, setSession, clearSession } = useSession()
    setSession('abc')
    clearSession()
    expect(sessionId.value).toBe('')
    expect(sessionStorage.getItem('totem.session_id')).toBeNull()
  })

  it('no longer carries the customer name — name is typed at checkout', () => {
    const session = useSession()
    expect('customerName' in session).toBe(false)
    session.setSession('abc')
    expect(sessionStorage.getItem('totem.customer_name')).toBeNull()
  })
})
