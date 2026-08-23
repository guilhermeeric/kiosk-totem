<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { formatMoney } from '../domain/money'
import { useSession } from '../composables/useSession'
import { useOrder } from '../composables/usePayment'
import { useItems } from '../composables/useItems'

const props = defineProps<{ id: string }>()

const router = useRouter()
const { clearSession } = useSession()
const { data: order } = useOrder(Number(props.id))
const { name } = useItems()

const DURATION_MS = 40_000
const TICK_MS = 250
const progress = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

function finish() {
  clearSession()
  router.push({ name: 'start' })
}

onMounted(() => {
  timer = setInterval(() => {
    progress.value = Math.min(100, progress.value + (100 * TICK_MS) / DURATION_MS)
    if (progress.value >= 100) {
      if (timer) clearInterval(timer)
      finish()
    }
  }, TICK_MS)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

function paymentKey(p: { id: number | null; method: string }): string {
  return p.id != null ? String(p.id) : p.method
}
</script>

<template>
  <div v-if="order" class="mx-auto flex min-h-screen max-w-md flex-col gap-6 p-6">
    <div class="mt-8 flex flex-col items-center gap-2 text-center">
      <p class="text-muted-foreground">Order number</p>
      <p class="text-7xl font-black tracking-wider text-amber-600">{{ order.id }}</p>
      <p class="text-muted-foreground">
        {{ order.customer_name }} · {{ order.order_type.replace('_', ' ') }}
      </p>
    </div>

    <div class="flex flex-col gap-2">
      <div class="h-3 overflow-hidden rounded-full bg-muted">
        <div
          class="h-full rounded-full bg-amber-500 transition-[width] duration-200 ease-linear"
          :style="{ width: `${progress}%` }"
        />
      </div>
      <p class="text-center text-muted-foreground">Preparing your order...</p>
    </div>

    <div class="flex flex-col gap-2 rounded-xl border border-border bg-card p-4 shadow-sm">
      <div v-for="line in order.items" :key="line.item_id" class="flex justify-between">
        <span>{{ line.quantity }}x {{ name(line.item_id) }}</span>
        <span>{{ formatMoney(line.total) }}</span>
      </div>
      <div class="mt-2 flex justify-between border-t border-border pt-2 font-bold">
        <span>Total</span>
        <span>{{ formatMoney(order.total) }}</span>
      </div>
    </div>

    <div class="flex flex-col gap-2 rounded-xl border border-border bg-card p-4 shadow-sm">
      <p class="text-muted-foreground">Payment</p>
      <p v-for="p in order.payments" :key="paymentKey(p)" class="flex justify-between">
        <span>{{ p.method.replace('_', ' ') }}</span>
        <span :class="p.status === 'PAID' ? 'text-green-600' : 'text-yellow-600'">
          {{ p.status }}
        </span>
      </p>
    </div>

    <button
      class="mt-auto rounded-xl bg-amber-500 py-4 text-xl font-semibold text-zinc-950 hover:bg-amber-400"
      @click="finish"
    >
      New order
    </button>
  </div>
  <p v-else class="p-6 text-muted-foreground">Loading receipt...</p>
</template>
