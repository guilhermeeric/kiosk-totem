import { describe, expect, it } from 'vitest'

import { overstockedLines } from '../stock'

function itemMap(entries: [number, number][]): Map<number, { stock: number }> {
  return new Map(entries.map(([id, stock]) => [id, { stock }]))
}

describe('overstockedLines', () => {
  it('returns nothing when quantities are within stock', () => {
    expect(
      overstockedLines(
        [
          { item_id: 1, quantity: 2 },
          { item_id: 2, quantity: 5 },
        ],
        itemMap([
          [1, 10],
          [2, 5],
        ]),
      ),
    ).toEqual([])
  })

  it('flags lines whose quantity exceeds stock, with the available count', () => {
    expect(
      overstockedLines([{ item_id: 1, quantity: 30 }], itemMap([[1, 2]])),
    ).toEqual([{ itemId: 1, quantity: 30, available: 2 }])
  })

  it('flags a cart holding a now-out-of-stock item', () => {
    expect(
      overstockedLines([{ item_id: 1, quantity: 1 }], itemMap([[1, 0]])),
    ).toEqual([{ itemId: 1, quantity: 1, available: 0 }])
  })

  it('ignores items it has no stock information for', () => {
    expect(overstockedLines([{ item_id: 999, quantity: 10 }], itemMap([]))).toEqual([])
  })
})
