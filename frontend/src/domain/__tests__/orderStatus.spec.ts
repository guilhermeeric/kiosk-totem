import { describe, expect, it } from 'vitest'

import { statusInfo } from '../orderStatus'

describe('statusInfo', () => {
  it('maps each order status to a label and progress step', () => {
    expect(statusInfo('PENDING')).toEqual({ label: 'Queued', step: 0 })
    expect(statusInfo('PREPARING')).toEqual({ label: 'Being prepared', step: 1 })
    expect(statusInfo('READY')).toEqual({ label: 'Ready — come pick up!', step: 2 })
    expect(statusInfo('COMPLETED')).toEqual({ label: 'Enjoy!', step: 3 })
  })

  it('marks cancelled orders as cancelled, with no progress steps', () => {
    expect(statusInfo('CANCELLED')).toEqual({ label: 'Cancelled', cancelled: true })
  })

  it('falls back to the raw status for unknown values', () => {
    expect(statusInfo('BOGUS')).toEqual({ label: 'BOGUS', step: 0 })
  })
})
