<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '../api/client'
import { handoffMode } from '../domain/handoff'
import { useSession } from '../composables/useSession'

const route = useRoute()
const router = useRouter()
const { setSession } = useSession()

const sessionId = computed(() => String(route.params.sessionId ?? ''))
const mode = computed(() => handoffMode(sessionId.value))

/** Adopt the totem's session on this device and continue on the menu. */
function adopt() {
  setSession(sessionId.value.trim())
  // Tell the totem it can reset now. Fire-and-forget: if it fails, the
  // totem's grace timer still frees the kiosk.
  api.markHandedOff(sessionId.value.trim()).catch(() => {})
  router.push({ name: 'menu' })
}

if (mode.value === 'adopt') {
  adopt()
}
</script>

<template>
  <div class="flex min-h-screen flex-col items-center justify-center gap-6 bg-background p-6">
    <template v-if="mode === 'invalid'">
      <h1 class="text-2xl font-bold">Invalid handoff link</h1>
      <p class="text-muted-foreground">
        This link is missing the session. Scan the QR on the totem to continue your order.
      </p>
      <button
        class="rounded-xl bg-amber-500 px-8 py-3 font-semibold text-zinc-950 transition hover:bg-amber-400"
        @click="router.push({ name: 'start' })"
      >
        Back to start
      </button>
    </template>

    <p v-else class="text-muted-foreground">Continuing...</p>
  </div>
</template>
