import { describe, expect, it } from 'vitest'

import { formatMoney } from '../money'

const NBSP = '\u00A0'

describe('formatMoney', () => {
  it('formats a decimal string as BRL currency', () => {
    expect(formatMoney('14.99')).toBe(`R$${NBSP}14,99`)
  })

  it('formats zero', () => {
    expect(formatMoney('0')).toBe(`R$${NBSP}0,00`)
  })

  it('formats large totals', () => {
    expect(formatMoney('1234.50')).toBe(`R$${NBSP}1.234,50`)
  })
})
