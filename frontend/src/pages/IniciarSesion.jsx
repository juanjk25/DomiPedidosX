import { useState } from 'react'
import { api, clearSession, saveTokens } from '../api.js'
import AuthLayout from '../components/AuthLayout.jsx'

export default function IniciarSesion({ onAuthenticated, navigate, notice }) {
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [visible, setVisible] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  async function submit(event) {
    event.preventDefault()
    if (busy) return
    setError('')
    const missing = {}
    if (!identifier.trim()) missing.username = 'Escribe tu correo electrónico o usuario.'
    if (!password) missing.password = 'Escribe tu contraseña.'
    setFieldErrors(missing)
    if (Object.keys(missing).length) {
      event.currentTarget.elements[Object.keys(missing)[0]]?.focus()
      return
    }
    setBusy(true)
    try {
      const username = identifier.includes('@') ? identifier.trim().toLowerCase() : identifier.trim()
      if (!username) throw new Error('Escribe tu correo o usuario.')
      const tokens = await api('/auth/login/', { auth: false, method: 'POST', body: JSON.stringify({ username, password }) })
      saveTokens(tokens)
      await onAuthenticated()
    } catch (err) {
      clearSession()
      setError(err.status === 401 ? 'Correo, usuario o contraseña incorrectos, o cuenta inactiva.' : err.message)
    } finally { setBusy(false) }
  }
  return <AuthLayout title="Qué bueno verte" description="Inicia sesión para descubrir el menú de hoy.">
    {notice && <p className="status-message" role="status">{notice}</p>}
    <form onSubmit={submit} aria-busy={busy} noValidate>
      <label htmlFor="login-username">Correo electrónico o usuario</label>
      <input id="login-username" name="username" value={identifier} onChange={e => { setIdentifier(e.target.value); setFieldErrors(old => ({ ...old, username: '' })) }} autoComplete="username" maxLength={150} required aria-invalid={!!fieldErrors.username} aria-describedby={fieldErrors.username ? 'login-username-error' : undefined} />
      {fieldErrors.username && <small className="field-error" id="login-username-error">{fieldErrors.username}</small>}
      <label htmlFor="login-password">Contraseña</label>
      <input id="login-password" name="password" type={visible ? 'text' : 'password'} value={password} onChange={e => { setPassword(e.target.value); setFieldErrors(old => ({ ...old, password: '' })) }} autoComplete="current-password" required aria-invalid={!!fieldErrors.password} aria-describedby={fieldErrors.password ? 'login-password-error' : undefined} />
      {fieldErrors.password && <small className="field-error" id="login-password-error">{fieldErrors.password}</small>}
      <button type="button" className="inline-link" aria-pressed={visible} onClick={() => setVisible(!visible)}>{visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}</button>
      {error && <p className="error-message" role="alert">{error}</p>}
      <button className="primary-button" disabled={busy}>{busy ? 'Ingresando…' : 'Iniciar sesión'}</button>
    </form>
    <button className="link-button" onClick={() => navigate('/recuperar-contrasena')}>¿Olvidaste tu contraseña?</button>
    <button className="link-button" onClick={() => navigate('/registro')}>Crear una cuenta de cliente</button>
  </AuthLayout>
}
