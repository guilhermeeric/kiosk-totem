<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'
import { Smartphone, X } from 'lucide-vue-next'

import { api } from '../api/client'
import { buildHandoffUrl, buildQrUrl } from '../domain/handoff'
import { useSession } from '../composables/useSession'

const props = defineProps<{ sessionId: string }>()
const emit = defineEmits<{ close: [] }>()

const router = useRouter()
const queryClient = useQueryClient()
const { clearSession } = useSession()

const GRACE_MS = 60_000
const TICK_MS = 250
const POLL_MS = 2_000

// Browser-only testing affordance: a new tab has its own sessionStorage, so it
// behaves exactly like another device (the "phone"). Gated by VITE_DEBUG.
const isDebug = import.meta.env.VITE_DEBUG === 'true'

const confirmed = ref(false)
const progress = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

// Captured at setup: confirmHandoff() calls clearSession(), which empties the
// session prop reactively — but the poll must keep tracking the ORIGINAL
// session the QR was built from.
const handoffSessionId = props.sessionId

const handoffUrl = buildHandoffUrl({
  origin: window.location.origin,
  sessionId: handoffSessionId,
})

// Poll the cart: the phone marks it handed off the moment it adopts the
// session, so the totem resets immediately instead of waiting the grace out.
const cartPoll = useQuery({
  queryKey: ['cart-handoff', handoffSessionId],
  queryFn: () => api.getCart(handoffSessionId),
  enabled: () => confirmed.value,
  refetchInterval: POLL_MS,
})

watch(cartPoll.data, (cart) => {
  if (cart?.handed_off_at != null) finish()
})

/** Close the overlay AND leave for the start screen, regardless of navigation. */
function finish() {
  if (timer) clearInterval(timer)
  queryClient.removeQueries({ queryKey: ['cart-handoff', handoffSessionId] })
  emit('close')
  router.push({ name: 'start' })
}

function confirmHandoff() {
  confirmed.value = true
  clearSession()
  timer = setInterval(() => {
    progress.value = Math.min(100, progress.value + (100 * TICK_MS) / GRACE_MS)
    if (progress.value >= 100) {
      finish()
    }
  }, TICK_MS)
}

function openInBrowser() {
  window.open(handoffUrl, '_blank')
}

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6">
    <div class="flex w-full max-w-md flex-col gap-4 rounded-2xl border border-border bg-card p-6 shadow-xl">
      <!-- Confirm step: deliberate, so nobody hands off by accident -->
      <template v-if="!confirmed">
        <div class="flex items-center gap-3">
          <div class="rounded-full bg-amber-500/20 p-3">
            <Smartphone class="h-7 w-7 text-amber-600" />
          </div>
          <h2 class="text-xl font-bold">Continue on your phone?</h2>
        </div>
        <p class="text-muted-foreground">
          Your order will move to your phone. The totem will reset for the next customer.
        </p>
        <div class="flex gap-3">
          <button
            class="flex-1 rounded-xl bg-muted py-3 font-semibold transition hover:bg-accent"
            @click="emit('close')"
          >
            Not now
          </button>
          <button
            class="flex-1 rounded-xl bg-amber-500 py-3 font-semibold text-zinc-950 transition hover:bg-amber-400"
            @click="confirmHandoff"
          >
            Continue
          </button>
        </div>
      </template>

      <!-- QR step: scan with the phone, then the totem returns to start -->
      <template v-else>
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-bold">Scan with your phone</h2>
          <button
            class="rounded-full p-2 text-muted-foreground hover:bg-muted"
            aria-label="Close"
            @click="finish"
          >
            <X class="h-5 w-5" />
          </button>
        </div>
        <div class="flex justify-center rounded-2xl border border-border bg-white p-4">
          <img :src="buildQrUrl(handoffUrl)" alt="Handoff QR code" class="h-56 w-56" />
        </div>
        <template v-if="isDebug">
          <button
            class="rounded-xl border border-border bg-muted py-2.5 font-semibold transition hover:bg-accent"
            @click="openInBrowser"
          >
            Test in browser (new tab)
          </button>
          <p class="break-all text-center text-xs text-muted-foreground">{{ handoffUrl }}</p>
        </template>
        <div class="h-2 overflow-hidden rounded-full bg-muted">
          <div
            class="h-full rounded-full bg-amber-500 transition-[width] duration-200 ease-linear"
            :style="{ width: `${progress}%` }"
          />
        </div>
        <p class="text-center text-sm text-muted-foreground">
          Returning to start shortly
        </p>
      </template>
    </div>
  </div>
</template>
