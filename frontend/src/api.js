const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'
export function getToken() { return localStorage.getItem('domi_access') }
export async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  const payload = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) {
    const detail = payload?.detail || Object.entries(payload || {})
      .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`)
      .join(' ')
    throw new Error(detail || 'No se pudo completar la solicitud.')
  }
  return payload
}
