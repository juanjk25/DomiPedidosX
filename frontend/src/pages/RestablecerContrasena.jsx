import { useState } from 'react'
import { api, clearSession } from '../api.js'
import AuthLayout from '../components/AuthLayout.jsx'

export default function RestablecerContrasena({ navigate, onReset }) {
  const params = new URLSearchParams(window.location.search)
  const uid = params.get('uid'), token = params.get('token')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')
  async function submit(event) {
    event.preventDefault()
    if (busy) return
    setError('')
    if (password !== confirmation) { setError('Las contraseñas no coinciden.'); return }
    setBusy(true)
    try {
      await api('/auth/password-reset/confirm/', { auth: false, method: 'POST', body: JSON.stringify({ uid, token, new_password: password }) })
      clearSession(); onReset?.(); setPassword(''); setConfirmation(''); setDone(true)
      // Retira el token del historial de la página al completar el cambio.
      window.history.replaceState({}, '', '/restablecer-contrasena')
    } catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }
  return <AuthLayout title="Elige tu nueva contraseña" description="Usa al menos 8 caracteres y evita contraseñas comunes o solo numéricas.">
    {done ? <p className="status-message" role="status">Tu contraseña se actualizó correctamente. Ya puedes iniciar sesión.</p>
      : !uid || !token ? <p className="error-message" role="alert">El enlace está incompleto. Solicita uno nuevo.</p>
        : <form onSubmit={submit} aria-busy={busy}>
          <label>Nueva contraseña<input type="password" autoComplete="new-password" minLength={8} value={password} onChange={e => setPassword(e.target.value)} required /></label>
          <label>Confirmar nueva contraseña<input type="password" autoComplete="new-password" minLength={8} value={confirmation} onChange={e => setConfirmation(e.target.value)} required /></label>
          {error && <p className="error-message" role="alert">{error}</p>}
          <button className="primary-button" disabled={busy}>{busy ? 'Guardando…' : 'Guardar nueva contraseña'}</button>
        </form>}
    {!done && <button className="link-button" onClick={() => navigate('/recuperar-contrasena')}>Solicitar otro enlace</button>}
    <button className="link-button" onClick={() => navigate('/login')}>Volver a iniciar sesión</button>
  </AuthLayout>
}
