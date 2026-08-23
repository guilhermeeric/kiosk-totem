import { ref } from 'vue'

const SESSION_KEY = 'totem.session_id'

// Module-level singleton: all views share the same session identity.
const sessionId = ref<string>(sessionStorage.getItem(SESSION_KEY) ?? '')

export function useSession() {
  function setSession(id: string) {
    sessionId.value = id
    sessionStorage.setItem(SESSION_KEY, id)
  }

  function clearSession() {
    sessionId.value = ''
    sessionStorage.removeItem(SESSION_KEY)
  }

  return { sessionId, setSession, clearSession }
}
