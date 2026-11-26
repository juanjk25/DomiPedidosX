import { useState } from 'react'
import { api } from '../api.js'
import AuthLayout from '../components/AuthLayout.jsx'

export default function RecuperarContrasena({ navigate }) {
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  async function submit(event) {
    event.preventDefault()
    if (busy) return
    setError(''); setBusy(true)
    try {
      await api('/auth/password-reset/', { auth: false, method: 'POST', body: JSON.stringify({ email: email.trim() }) })
      setSent(true)
    } catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }
  return <AuthLayout title="Recupera tu cuenta" description="Escribe el correo que registraste y te enviaremos un enlace para cambiar tu contraseña.">
    {sent ? <div className="status-message" role="status"><strong>Solicitud recibida</strong><p>Si existe una cuenta con ese correo, enviaremos un enlace de recuperación. Revisa también la carpeta de spam.</p><button type="button" className="inline-link" onClick={() => setSent(false)}>Usar otro correo</button></div>
      : <form onSubmit={submit} aria-busy={busy}>
        <label>Correo electrónico registrado<input type="email" name="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} maxLength={100} required /></label>
        {error && <p className="error-message" role="alert">{error}</p>}
        <button className="primary-button" disabled={busy}>{busy ? 'Enviando…' : 'Enviar enlace de recuperación'}</button>
      </form>}
    <button className="link-button" onClick={() => navigate('/login')}>Volver a iniciar sesión</button>
  </AuthLayout>
}
