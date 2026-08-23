<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import { api } from '../api/client'
import type { components } from '../domain/api'
import { formatMoney } from '../domain/money'
import { timeAgo } from '../domain/time'
import { useItems } from '../composables/useItems'

type OrderStatus = components['schemas']['OrderStatus']

const queryClient = useQueryClient()
const { name } = useItems()

const REFETCH_MS = 5_000

const COLUMNS: { key: OrderStatus; title: string; action: string; next: OrderStatus }[] = [
  { key: 'PENDING', title: 'New', action: 'Start preparing', next: 'PREPARING' },
  { key: 'PREPARING', title: 'Preparing', action: 'Done', next: 'READY' },
  { key: 'READY', title: 'Ready', action: 'Picked up', next: 'COMPLETED' },
]

const columns = COLUMNS.map((col) => ({
  ...col,
  query: useQuery({
    queryKey: ['orders', col.key],
    queryFn: () => api.listOrders(col.key),
    refetchInterval: REFETCH_MS,
  }),
}))

const transition = useMutation({
  mutationFn: (input: { orderId: number; status: OrderStatus }) =>
    api.updateOrderStatus(input.orderId, input.status),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['orders'] })
  },
})
</script>

<template>
  <div class="flex h-screen flex-col bg-background">
    <header class="flex items-center justify-between border-b border-border bg-card px-6 py-4">
      <div class="flex items-center gap-2">
        <span class="text-xl font-bold">Kitchen</span>
        <span class="rounded-full bg-amber-500/20 px-3 py-1 text-sm font-semibold text-amber-700">
          live · 5s
        </span>
      </div>
    </header>

    <main class="grid flex-1 grid-cols-3 gap-4 overflow-y-auto p-4">
      <section v-for="col in columns" :key="col.key" class="flex flex-col gap-3">
        <h2 class="flex items-center justify-between px-1 text-lg font-bold">
          {{ col.title }}
          <span class="rounded-full bg-muted px-2.5 py-0.5 text-sm font-semibold">
            {{ col.query.data.value?.length ?? 0 }}
          </span>
        </h2>

        <div v-if="col.query.isPending.value" class="space-y-3">
          <div v-for="i in 2" :key="i" class="h-36 animate-pulse rounded-xl bg-muted" />
        </div>

        <div v-else class="flex flex-col gap-3">
          <div
            v-for="order in col.query.data.value ?? []"
            :key="String(order.id)"
            class="flex flex-col gap-2 rounded-xl border border-border bg-card p-4 shadow-sm"
          >
            <div class="flex items-start justify-between gap-2">
              <span class="text-3xl font-black text-amber-600">#{{ order.id }}</span>
              <span class="text-sm text-muted-foreground">{{ timeAgo(order.created_at) }}</span>
            </div>
            <p class="font-semibold">{{ order.customer_name }}</p>
            <p class="text-sm text-muted-foreground">{{ order.order_type.replace('_', ' ') }}</p>
            <ul class="flex flex-col gap-1 border-t border-border pt-2 text-sm">
              <li v-for="line in order.items" :key="line.item_id" class="flex justify-between gap-2">
                <span class="truncate">{{ line.quantity }}x {{ name(line.item_id) }}</span>
                <span class="shrink-0 font-medium">{{ formatMoney(line.total) }}</span>
              </li>
            </ul>
            <div class="mt-1 flex items-center justify-between border-t border-border pt-2">
              <span class="font-bold">{{ formatMoney(order.total) }}</span>
              <button
                class="rounded-lg bg-amber-500 px-4 py-2 font-semibold text-zinc-950 transition hover:bg-amber-400 disabled:opacity-50"
                :disabled="transition.isPending.value"
                @click="
                  transition.mutate({ orderId: order.id as number, status: col.next })
                "
              >
                {{ col.action }}
              </button>
            </div>
          </div>
          <p v-if="(col.query.data.value?.length ?? 0) === 0" class="px-1 text-muted-foreground">
            Nothing here.
          </p>
        </div>
      </section>
    </main>
  </div>
</template>
