const API_URL = (import.meta.env?.VITE_API_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '')
export function getToken() { return localStorage.getItem('domi_access') }
export function saveTokens(tokens) {
  localStorage.setItem('domi_access', tokens.access)
  if (tokens.refresh) localStorage.setItem('domi_refresh', tokens.refresh)
}
export function clearSession() {
  localStorage.removeItem('domi_access')
  localStorage.removeItem('domi_refresh')
}
export class ApiError extends Error {
  constructor(message, status, fields = {}) {
    super(message)
    this.status = status
    this.fields = fields
  }
}
let refreshing
async function refreshAccess() {
  if (!refreshing) {
    refreshing = (async () => {
      const refresh = localStorage.getItem('domi_refresh')
      if (!refresh) return false
      try {
        const response = await fetch(`${API_URL}/auth/token/refresh/`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh }),
        })
        if (!response.ok) return false
        saveTokens(await response.json())
        return true
      } catch { return false }
    })().finally(() => { refreshing = null })
  }
  return refreshing
}
export async function api(path, { auth = true, retry = true, ...options } = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  if (auth && getToken()) headers.Authorization = `Bearer ${getToken()}`
  let response
  try { response = await fetch(`${API_URL}${path}`, { ...options, headers }) }
  catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError('No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.', 0)
  }
  if (response.status === 401 && auth) {
    if (retry && await refreshAccess()) return api(path, { ...options, auth, retry: false })
    clearSession()
    if (typeof window !== 'undefined') window.dispatchEvent(new Event('domi:session-expired'))
  }
  const payload = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) {
    const detail = payload?.detail || Object.entries(payload || {})
      .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`).join(' ')
    throw new ApiError(detail || 'No se pudo completar la solicitud.', response.status, payload || {})
  }
  return payload
}
