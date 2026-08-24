/** Cart-level availability: which cart lines exceed the current item stock.

 * Advisory UI, not an invariant — the authoritative gate is the backend's
 * consume_stock at checkout (which also catches races the client cannot see).
 * Unknown item ids are skipped: the client cannot judge availability for them.
 */

export type CartLineQty = { item_id: number; quantity: number }
export type StockRef = { stock: number }

export type OverstockedLine = {
  itemId: number
  quantity: number
  available: number
}

export function overstockedLines(
  lines: CartLineQty[],
  itemById: ReadonlyMap<number, StockRef>,
): OverstockedLine[] {
  const result: OverstockedLine[] = []
  for (const line of lines) {
    const item = itemById.get(line.item_id)
    if (item !== undefined && line.quantity > item.stock) {
      result.push({ itemId: line.item_id, quantity: line.quantity, available: item.stock })
    }
  }
  return result
}
