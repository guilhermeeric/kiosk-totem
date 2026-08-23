<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { UtensilsCrossed } from 'lucide-vue-next'

import { api } from '../api/client'

const READY_QUERY = { queryKey: ['orders', 'READY'] } as const

const readyQuery = useQuery({
  queryKey: READY_QUERY.queryKey,
  queryFn: () => api.listOrders('READY'),
  refetchInterval: 3_000,
})

/** Visor shows the current ready order: the oldest one waiting for pickup. */
const current = computed(() => readyQuery.data.value?.[0] ?? null)
</script>

<template>
  <div
    class="flex h-screen flex-col items-center justify-center gap-10 bg-background px-8 text-center"
  >
    <template v-if="current">
      <p class="text-2xl font-semibold text-muted-foreground">Order ready — please come pick up</p>
      <p class="text-[12rem] font-black leading-none tracking-tight text-amber-500">
        {{ current.id }}
      </p>
      <p class="text-4xl font-bold">{{ current.customer_name }}</p>
      <p class="text-2xl text-muted-foreground">{{ current.order_type.replace('_', ' ') }}</p>
    </template>

    <template v-else>
      <div class="rounded-full bg-muted p-6">
        <UtensilsCrossed class="h-16 w-16 text-muted-foreground" />
      </div>
      <p class="text-5xl font-bold text-muted-foreground">No orders ready</p>
      <p class="text-2xl text-muted-foreground/70">Your order will appear here when it's done.</p>
    </template>
  </div>
</template>
