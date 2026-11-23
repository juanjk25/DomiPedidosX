import { useEffect, useState } from 'react'
import { api } from '../api.js'

const emptyProfile = {
  email: '',
  nombres: '',
  apellidos: '',
  tipo_documento: 'CC',
  numero_documento: '',
  telefono_cliente: '',
  extension_telefonica: '',
  direccion_residencia: '',
  referencia_direccion: '',
  latitud: '',
  longitud: '',
  fecha_nacimiento: '',
}

export default function MiCuenta({ user, onUpdated, onBack, onLogout }) {
  const [form, setForm] = useState({ ...emptyProfile, ...user })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })
  const [changingPassword, setChangingPassword] = useState(false)
  const [passwordError, setPasswordError] = useState('')
  const [passwordSuccess, setPasswordSuccess] = useState('')

  useEffect(() => {
    let current = true
    api('/me/')
      .then(profile => {
        if (!current) return
        setForm({
          ...emptyProfile,
          ...profile,
          telefono_cliente: profile.telefono_cliente ?? profile.telefono ?? '',
        })
      })
      .catch(err => { if (current) setError(err.message) })
      .finally(() => { if (current) setLoading(false) })
    return () => { current = false }
  }, [])

  function change(event) {
    const { name, value } = event.target
    const nextValue = ['nombres', 'apellidos'].includes(name)
      ? value.replace(/[^\p{L} ]/gu, '')
      : value
    setForm(current => ({ ...current, [name]: nextValue }))
  }

  async function guardar(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      const profile = await api('/me/', {
        method: 'PATCH',
        body: JSON.stringify({
          ...form,
          latitud: form.latitud === '' ? null : form.latitud,
          longitud: form.longitud === '' ? null : form.longitud,
          telefono_cliente: form.telefono_cliente,
        }),
      })
      onUpdated(profile)
      setSuccess('Tus datos se actualizaron correctamente.')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  function changePassword(event) {
    const { name, value } = event.target
    setPasswordForm(current => ({ ...current, [name]: value }))
  }

  async function guardarPassword(event) {
    event.preventDefault()
    setChangingPassword(true)
    setPasswordError('')
    setPasswordSuccess('')
    try {
      if (passwordForm.new_password !== passwordForm.confirm_password) {
        setPasswordError('Las contraseñas nuevas no coinciden.')
        return
      }
      const result = await api('/auth/password-change/', {
        method: 'POST',
        body: JSON.stringify(passwordForm),
      })
      setPasswordSuccess(result.message)
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' })
    } catch (err) {
      setPasswordError(err.message)
    } finally {
      setChangingPassword(false)
    }
  }

  return (
    <section className="account-page">
      <aside className="account-sidebar">
        <div className="menu-sidebar-brand"><span className="brand-mark">D</span>DomiPedidos<span className="brand-x">X</span></div>
        <span className="menu-sidebar-label">02 / CLIENTE</span>
        <button className="menu-nav" onClick={onBack}>⌁ <span>Pedir pedido</span></button>
        <button className="menu-nav">▤ <span>Mis pedidos</span></button>
        <button className="menu-nav active">♙ <span>Mi cuenta</span></button>
        <button className="menu-logout" onClick={onLogout}>Cerrar sesión</button>
      </aside>

      <main className="account-main">
        <div className="menu-page-top"><span>02 / CLIENTE · MI CUENTA</span></div>
        <div className="account-heading">
          <div>
            <span className="account-kicker">PERFIL PERSONAL</span>
            <h1>Edita tu información</h1>
            <p>Mantén tus datos de contacto y entrega siempre actualizados.</p>
          </div>
          <div className="account-avatar">{form.nombres?.[0] || 'C'}{form.apellidos?.[0] || ''}</div>
        </div>

        <form className="account-password-form" onSubmit={guardarPassword}>
          <fieldset>
            <legend>Cambiar contraseña</legend>
            {passwordSuccess && <div className="account-success" role="status">✓ <span>{passwordSuccess}</span></div>}
            {passwordError && <p className="account-error" role="alert">{passwordError}</p>}
            <div className="account-password-fields">
              <label>Contraseña actual<input type="password" name="current_password" value={passwordForm.current_password} onChange={changePassword} autoComplete="current-password" required /></label>
              <label>Nueva contraseña<input type="password" name="new_password" value={passwordForm.new_password} onChange={changePassword} autoComplete="new-password" minLength={8} required /></label>
              <label>Confirmar nueva contraseña<input type="password" name="confirm_password" value={passwordForm.confirm_password} onChange={changePassword} autoComplete="new-password" minLength={8} required /></label>
            </div>
            <div className="account-actions account-password-actions">
              <button type="submit" className="account-save" disabled={changingPassword}>{changingPassword ? 'Cambiando…' : 'Cambiar contraseña'}</button>
            </div>
          </fieldset>
        </form>

        {loading ? (
          <p className="account-loading" role="status">Cargando tus datos…</p>
        ) : (
          <form className="account-form" onSubmit={guardar}>
            {success && <div className="account-success" role="status">✓ <span>{success}</span></div>}
            {error && <p className="account-error" role="alert">{error}</p>}

            <fieldset>
              <legend>Datos personales</legend>
              <div className="account-fields">
                <label>Correo registrado<input type="email" name="email" value={form.email} onChange={change} required /></label>
                <label>Nombres<input name="nombres" value={form.nombres} onChange={change} required /></label>
                <label>Apellidos<input name="apellidos" value={form.apellidos} onChange={change} required /></label>
                <label>Fecha de nacimiento<input type="date" name="fecha_nacimiento" value={form.fecha_nacimiento} onChange={change} required /></label>
                <label>Tipo de documento<select name="tipo_documento" value={form.tipo_documento} disabled><option>CC</option><option>CE</option><option>NIT</option><option>TI</option></select></label>
                <label>Número de documento<input name="numero_documento" value={form.numero_documento} onChange={change} required /></label>
              </div>
            </fieldset>

            <fieldset>
              <legend>Contacto y entrega</legend>
              <div className="account-fields">
                <label>Teléfono<input name="telefono_cliente" value={form.telefono_cliente} onChange={change} /></label>
                <label>Extensión telefónica<input name="extension_telefonica" value={form.extension_telefonica} onChange={change} /></label>
                <label className="account-wide">Dirección de residencia<input name="direccion_residencia" value={form.direccion_residencia} onChange={change} /></label>
                <label className="account-wide">Referencia de dirección<input name="referencia_direccion" value={form.referencia_direccion} onChange={change} /></label>
                <label>Latitud<input type="number" step="0.000001" name="latitud" value={form.latitud ?? ''} onChange={change} /></label>
                <label>Longitud<input type="number" step="0.000001" name="longitud" value={form.longitud ?? ''} onChange={change} /></label>
              </div>
            </fieldset>

            <div className="account-actions">
              <button type="button" className="secondary-button" onClick={onBack}>Cancelar</button>
              <button type="submit" className="account-save" disabled={saving}>{saving ? 'Guardando…' : 'Guardar cambios'}</button>
            </div>
          </form>
        )}

      </main>
    </section>
  )
}
