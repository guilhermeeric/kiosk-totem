<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { buildQrUrl, buildTrackUrl } from '../domain/handoff'
import { formatMoney } from '../domain/money'
import { useCart } from '../composables/useCart'
import { useSession } from '../composables/useSession'
import { useOrder } from '../composables/useOrder'
import { useItems } from '../composables/useItems'

const props = defineProps<{ id: string }>()

const router = useRouter()
const { clearSession } = useSession()
const { data: order, error } = useOrder(Number(props.id))
const { name } = useItems()
const { cartQuery } = useCart()

// The receipt is the only moment the order id surfaces, so the tracking QR is
// always shown. On a phone (cart handed off), a direct link is shown instead
// of making the customer scan their own screen. 40s grace: the QR must be
// scanned in the receipt window — the printerless kiosk tradeoff.
const trackUrl = buildTrackUrl({ origin: window.location.origin, orderId: Number(props.id) })
const onPhone = () => cartQuery.data.value?.handed_off_at != null

// Browser-only testing affordance, same as the handoff overlay: a new tab has
// its own session, so it behaves like another device (the "phone").
const isDebug = import.meta.env.VITE_DEBUG === 'true'

function openTrackInBrowser() {
  window.open(trackUrl, '_blank')
}

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
      <p class="text-center text-muted-foreground">
        Order sent to the kitchen — watch the screen for your number
      </p>
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

    <div class="flex flex-col items-center gap-3 rounded-xl border border-border bg-card p-4 shadow-sm">
      <p class="font-semibold">Track on your phone</p>
      <img
        :src="buildQrUrl(trackUrl)"
        alt="Order tracking QR"
        class="h-44 w-44 rounded-lg bg-white p-2"
      />
      <a v-if="onPhone()" :href="'/track/' + order.id" class="text-sm font-semibold text-amber-600 underline">
        Track your order
      </a>
      <template v-if="isDebug">
        <button
          class="rounded-xl border border-border bg-muted px-4 py-2 text-sm font-semibold transition hover:bg-accent"
          @click="openTrackInBrowser"
        >
          Test in browser (new tab)
        </button>
        <p class="break-all text-center text-xs text-muted-foreground">{{ trackUrl }}</p>
      </template>
    </div>

    <button
      class="mt-auto rounded-xl bg-amber-500 py-4 text-xl font-semibold text-zinc-950 hover:bg-amber-400"
      @click="finish"
    >
      New order
    </button>
  </div>
  <p v-else-if="error" class="p-6 text-muted-foreground">Order not found.</p>
  <p v-else class="p-6 text-muted-foreground">Loading receipt...</p>
</template>
