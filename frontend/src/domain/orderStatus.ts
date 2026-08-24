/** Order status presentation: human label + 4-step progress position.
 *
 * Pure mapping, no I/O. The backend owns the status lifecycle; this module
 * only renders it. CANCELLED has no progress position.
 */

export type StatusInfo = { label: string; step?: number; cancelled?: boolean }

const STATUS_INFO: Record<string, { label: string; step: number }> = {
  PENDING: { label: 'Queued', step: 0 },
  PREPARING: { label: 'Being prepared', step: 1 },
  READY: { label: 'Ready — come pick up!', step: 2 },
  COMPLETED: { label: 'Enjoy!', step: 3 },
}

export function statusInfo(status: string): StatusInfo {
  if (status === 'CANCELLED') return { label: 'Cancelled', cancelled: true }
  return STATUS_INFO[status] ?? { label: status, step: 0 }
}
