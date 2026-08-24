<script setup lang="ts">
import { computed } from 'vue'

import { statusInfo } from '../domain/orderStatus'
import { useOrder } from '../composables/usePayment'

const props = defineProps<{ id: string }>()

// Status changes are slow (minutes), so a 5s poll is plenty — same polling
// approach as kitchen (5s; visor polls 3s). No WebSocket anywhere.
const POLL_MS = 5_000
const { data: order, isPending, error } = useOrder(Number(props.id), POLL_MS)

const info = computed(() => (order.value ? statusInfo(order.value.status) : null))
</script>

<template>
  <div class="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-8 p-6 text-center">
    <p v-if="isPending" class="text-muted-foreground">Loading...</p>
    <p v-else-if="error || !order" class="text-muted-foreground">Order not found.</p>

    <template v-else>
      <div class="flex flex-col items-center gap-2">
        <p class="text-muted-foreground">Order</p>
        <p class="text-7xl font-black tracking-wider text-amber-600">{{ order.id }}</p>
        <p class="text-muted-foreground">
          {{ order.customer_name }} · {{ order.order_type.replace('_', ' ') }}
        </p>
      </div>

      <p class="text-2xl font-bold">{{ info?.label }}</p>

      <div v-if="!info?.cancelled" class="flex w-full gap-2">
        <div
          v-for="i in 4"
          :key="i"
          class="h-3 flex-1 rounded-full"
          :class="i <= (info?.step ?? 0) + 1 ? 'bg-amber-500' : 'bg-muted'"
        />
      </div>
      <p v-else class="text-destructive">This order was cancelled.</p>
    </template>
  </div>
</template>
