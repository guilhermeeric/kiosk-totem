<script setup lang="ts">
import { ref } from 'vue'
import { CheckCircle2, Loader2, XCircle } from 'lucide-vue-next'

import { formatMoney } from '../domain/money'

const props = defineProps<{
  amount: string
  method: string
  debug: boolean
  state: 'pick' | 'processing' | 'approved' | 'declined'
}>()

const emit = defineEmits<{ choose: [status: 'PAID' | 'FAILED']; retry: [] }>()

const METHOD_EMOJI: Record<string, string> = {
  PIX: '📱',
  CREDIT_CARD: '💳',
  DEBIT_CARD: '💳',
  CASH: '💵',
}

// Cosmetic only: both failures map to FAILED on the wire.
const failureFlavor = ref<'declined' | 'network'>('declined')

function pick(status: 'PAID' | 'FAILED', flavor: 'declined' | 'network' = 'declined') {
  failureFlavor.value = flavor
  emit('choose', status)
}
</script>

<template>
  <div class="flex flex-col items-center gap-6">
    <!-- Fake card machine -->
    <div class="w-full max-w-sm rounded-3xl bg-zinc-900 p-6 text-white shadow-2xl">
      <div class="flex items-center justify-between text-xs uppercase tracking-widest text-zinc-400">
        <span>Totem Pay</span>
        <span>{{ method }}</span>
      </div>
      <div class="my-6 flex flex-col items-center gap-3">
        <span class="text-6xl">{{ METHOD_EMOJI[method] ?? '💳' }}</span>
        <span class="text-3xl font-black">{{ formatMoney(amount) }}</span>
      </div>

      <div v-if="state === 'processing'" class="flex items-center justify-center gap-2 text-amber-400">
        <Loader2 class="h-5 w-5 animate-spin" />
        <span class="font-semibold tracking-widest">APPROVING...</span>
      </div>
      <div v-else-if="state === 'approved'" class="flex items-center justify-center gap-2 text-emerald-400">
        <CheckCircle2 class="h-6 w-6" />
        <span class="font-semibold">Approved</span>
      </div>
      <div v-else-if="state === 'declined'" class="flex items-center justify-center gap-2 text-red-400">
        <XCircle class="h-6 w-6" />
        <span class="font-semibold">
          {{ failureFlavor === 'network' ? 'Network error' : 'Card declined' }}
        </span>
      </div>
    </div>

    <!-- Debug: pick the simulated outcome -->
    <template v-if="debug && state === 'pick'">
      <p class="font-semibold text-muted-foreground">Simulate payment outcome</p>
      <div class="flex flex-wrap justify-center gap-3">
        <button
          class="rounded-xl bg-emerald-500 px-4 py-3 font-semibold text-zinc-950 transition hover:bg-emerald-400"
          @click="pick('PAID')"
        >
          ✓ Approved
        </button>
        <button
          class="rounded-xl bg-red-500 px-4 py-3 font-semibold text-zinc-950 transition hover:bg-red-400"
          @click="pick('FAILED', 'declined')"
        >
          ✗ Declined
        </button>
        <button
          class="rounded-xl bg-muted px-4 py-3 font-semibold transition hover:bg-accent"
          @click="pick('FAILED', 'network')"
        >
          ⚠ Network error
        </button>
      </div>
    </template>

    <p v-else-if="state === 'declined'" class="text-sm text-muted-foreground">
      You can try again.
    </p>
    <p v-else-if="state === 'approved'" class="text-sm text-muted-foreground">
      Sending you to your receipt…
    </p>

    <button
      v-if="state === 'declined'"
      class="w-full max-w-sm rounded-xl bg-amber-500 py-4 text-xl font-bold text-zinc-950 transition hover:bg-amber-400"
      @click="emit('retry')"
    >
      Try again
    </button>
  </div>
</template>
