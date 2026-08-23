/** Format a Decimal-as-string (backend serializes money as str) as BRL currency. */
export function formatMoney(value: string): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(Number(value))
}
