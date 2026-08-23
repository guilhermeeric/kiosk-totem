import { ref } from 'vue'

const SESSION_KEY = 'totem.session_id'
const NAME_KEY = 'totem.customer_name'

// Module-level singleton: all views share the same session identity.
const sessionId = ref<string>(sessionStorage.getItem(SESSION_KEY) ?? '')
const customerName = ref<string>(sessionStorage.getItem(NAME_KEY) ?? '')

export function useSession() {
  function setSession(id: string, name: string) {
    sessionId.value = id
    customerName.value = name
    sessionStorage.setItem(SESSION_KEY, id)
    sessionStorage.setItem(NAME_KEY, name)
  }

  function clearSession() {
    sessionId.value = ''
    customerName.value = ''
    sessionStorage.removeItem(SESSION_KEY)
    sessionStorage.removeItem(NAME_KEY)
  }

  return { sessionId, customerName, setSession, clearSession }
}
