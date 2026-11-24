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

  const [showPasswordPanel, setShowPasswordPanel] = useState(false)
  const [showPasswords, setShowPasswords] = useState(false)
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
      <style>{`
        .account-page {
          display: grid;
          grid-template-columns: 250px minmax(0, 1fr);
          min-height: 100vh;
          background: #f5f4f0;
        }
        .account-sidebar {
          background: #17191e;
          color: #f8fafc;
          padding: 1.5rem 1.15rem;
          display: flex;
          flex-direction: column;
          gap: 0.45rem;
          position: sticky;
          top: 0;
          height: 100vh;
          box-sizing: border-box;
        }
        .account-sidebar .menu-logout {
          margin-top: auto;
        }
        .account-main {
          padding: 1.5rem 2.25rem 3rem;
          min-width: 0;
        }
        .dp-profile-shell {
          max-width: 820px;
          margin: 0 auto;
        }
        .dp-profile-card {
          background: #ffffff;
          border: 1px solid #eceef2;
          border-radius: 18px;
          box-shadow: 0 8px 28px rgba(15, 23, 42, 0.04);
          padding: 0 2.25rem 2rem;
        }
        .dp-profile-tabs {
          display: flex;
          border-bottom: 1px solid #eceef2;
          margin: 0 -2.25rem 1.75rem;
          padding: 0 2.25rem;
        }
        .dp-profile-tab {
          display: inline-block;
          border-bottom: 2.5px solid #d62828;
          padding: 1.15rem 0.15rem 0.95rem;
          font-size: 0.92rem;
          font-weight: 700;
          color: #d62828;
          margin-bottom: -1px;
        }
        .dp-profile-header {
          margin-bottom: 1.75rem;
        }
        .dp-profile-header h1 {
          font-size: 1.65rem;
          font-weight: 800;
          color: #0f172a;
          margin: 0 0 0.35rem;
          letter-spacing: -0.02em;
        }
        .dp-profile-header p {
          margin: 0;
          color: #64748b;
          font-size: 0.95rem;
        }
        .dp-section-head {
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          gap: 1rem;
          margin-bottom: 0.95rem;
        }
        .dp-section-head h2 {
          font-size: 1.02rem;
          font-weight: 700;
          color: #0f172a;
          margin: 0;
        }
        .dp-required-note {
          font-size: 0.78rem;
          color: #94a3b8;
        }
        .dp-grid-2 {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 1rem 1.25rem;
          margin-bottom: 1.65rem;
        }
        .dp-grid-address {
          display: grid;
          grid-template-columns: 1.55fr 1fr;
          gap: 1rem 1.25rem;
          margin-bottom: 1.65rem;
        }
        .dp-field {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }
        .dp-field label {
          font-size: 0.84rem;
          font-weight: 600;
          color: #1e293b;
        }
        .dp-field input,
        .dp-field select {
          width: 100%;
          height: 44px;
          padding: 0 0.9rem;
          border-radius: 10px;
          border: 1px solid #dfe3ea;
          background: #ffffff;
          font-size: 0.92rem;
          color: #0f172a;
          transition: border-color 0.15s ease, box-shadow 0.15s ease;
          box-sizing: border-box;
        }
        .dp-field input:focus,
        .dp-field select:focus {
          outline: none;
          border-color: #d62828;
          box-shadow: 0 0 0 3px rgba(214, 40, 40, 0.1);
        }
        .dp-field input:disabled,
        .dp-field select:disabled {
          background: #f8fafc;
          color: #64748b;
          cursor: not-allowed;
        }
        .dp-security-box {
          background: #f8fafc;
          border: 1px solid #eef2f6;
          border-radius: 12px;
          padding: 1rem 1.25rem;
          margin-bottom: 1.75rem;
        }
        .dp-security-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
        }
        .dp-security-info {
          display: flex;
          align-items: center;
          gap: 0.85rem;
        }
        .dp-security-icon {
          width: 34px;
          height: 34px;
          border-radius: 8px;
          background: #ffffff;
          border: 1px solid #e2e8f0;
          display: grid;
          place-items: center;
          color: #475569;
          flex-shrink: 0;
        }
        .dp-security-title {
          font-size: 0.92rem;
          font-weight: 700;
          color: #0f172a;
          margin: 0 0 0.15rem;
        }
        .dp-security-desc {
          font-size: 0.82rem;
          color: #64748b;
          margin: 0;
        }
        .dp-security-trigger {
          background: none;
          border: none;
          color: #d62828;
          font-weight: 700;
          font-size: 0.86rem;
          cursor: pointer;
          padding: 0.4rem 0.6rem;
          border-radius: 8px;
          white-space: nowrap;
        }
        .dp-security-trigger:hover {
          background: rgba(214, 40, 40, 0.07);
        }
        .dp-password-drawer {
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid #e2e8f0;
        }
        .dp-password-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 0.85rem;
          margin-bottom: 0.85rem;
        }
        .dp-password-footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 0.75rem;
          flex-wrap: wrap;
        }
        .dp-actions-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
          padding-top: 0.25rem;
        }
        .dp-btn-cancel {
          min-width: 175px;
          height: 46px;
          border-radius: 10px;
          border: 1px solid #e2e8f0;
          background: #f8fafc;
          color: #1e293b;
          font-weight: 700;
          font-size: 0.92rem;
          cursor: pointer;
          transition: background 0.15s ease;
        }
        .dp-btn-cancel:hover {
          background: #f1f5f9;
        }
        .dp-btn-save {
          min-width: 210px;
          height: 46px;
          padding: 0 1.5rem;
          border-radius: 10px;
          border: none;
          background: #d62828;
          color: #ffffff;
          font-weight: 700;
          font-size: 0.92rem;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 0.65rem;
          box-shadow: 0 6px 16px rgba(214, 40, 40, 0.22);
          transition: background 0.15s ease, transform 0.1s ease;
        }
        .dp-btn-save:hover:not(:disabled) {
          background: #b91c1c;
        }
        .dp-btn-save:disabled {
          opacity: 0.65;
          cursor: not-allowed;
        }
        .dp-protected-note {
          text-align: center;
          font-size: 0.8rem;
          color: #94a3b8;
          margin: 1rem 0 0;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.4rem;
        }
        @media (max-width: 900px) {
          .account-page {
            grid-template-columns: 1fr;
          }
          .account-sidebar {
            position: static;
            height: auto;
          }
        }
        @media (max-width: 760px) {
          .dp-profile-card {
            padding: 0 1.25rem 1.5rem;
          }
          .dp-profile-tabs {
            margin: 0 -1.25rem 1.5rem;
            padding: 0 1.25rem;
          }
          .dp-grid-2,
          .dp-grid-address,
          .dp-password-grid {
            grid-template-columns: 1fr;
          }
          .dp-security-row,
          .dp-actions-row {
            flex-direction: column;
            align-items: stretch;
          }
        }
      `}</style>

      <aside className="account-sidebar">
        <div className="menu-sidebar-brand">
          <span className="brand-mark">D</span>DomiPedidos<span className="brand-x">X</span>
        </div>
        <span className="menu-sidebar-label">02 / CLIENTE</span>
        <button className="menu-nav" onClick={onBack}>⌁ <span>Pedir pedido</span></button>
        <button className="menu-nav">▤ <span>Mis pedidos</span></button>
        <button className="menu-nav active">♙ <span>Mi cuenta</span></button>
        <button className="menu-logout" onClick={onLogout}>Cerrar sesión</button>
      </aside>

      <main className="account-main">
        <div className="menu-page-top"><span>02 / MI CUENTA</span></div>

        <div className="dp-profile-shell">
          <div className="dp-profile-card">
            <div className="dp-profile-tabs">
              <span className="dp-profile-tab">Editar perfil</span>
            </div>

            <div className="dp-profile-header">
              <h1>Tu perfil, siempre al día</h1>
              <p>Actualiza tus datos para seguir disfrutando de tus favoritos.</p>
            </div>

            {loading ? (
              <p className="account-loading" role="status">Cargando tus datos…</p>
            ) : (
              <>
                <form id="profile-edit-form" onSubmit={guardar}>
                  {success && (
                    <div className="account-success" role="status" style={{ marginBottom: '1rem' }}>
                      ✓ <span>{success}</span>
                    </div>
                  )}
                  {error && (
                    <p className="account-error" role="alert" style={{ marginBottom: '1rem' }}>
                      {error}
                    </p>
                  )}

                  {/* Sección: Datos personales */}
                  <div className="dp-section-head">
                    <h2>Datos personales</h2>
                    <span className="dp-required-note">* Campos obligatorios</span>
                  </div>

                  <div className="dp-grid-2">
                    <div className="dp-field">
                      <label htmlFor="pf-nombres">Nombres *</label>
                      <input
                        id="pf-nombres"
                        name="nombres"
                        value={form.nombres}
                        onChange={change}
                        required
                      />
                    </div>

                    <div className="dp-field">
                      <label htmlFor="pf-apellidos">Apellidos *</label>
                      <input
                        id="pf-apellidos"
                        name="apellidos"
                        value={form.apellidos}
                        onChange={change}
                        required
                      />
                    </div>

                    <div className="dp-field">
                      <label htmlFor="pf-email">Correo electrónico *</label>
                      <input
                        id="pf-email"
                        type="email"
                        name="email"
                        value={form.email}
                        onChange={change}
                        required
                      />
                    </div>

                    <div className="dp-field">
                      <label htmlFor="pf-telefono">Número de celular</label>
                      <input
                        id="pf-telefono"
                        name="telefono_cliente"
                        value={form.telefono_cliente}
                        onChange={change}
                        placeholder="Ej. 310 456 7890"
                      />
                    </div>

                    <div className="dp-field">
                      <label htmlFor="pf-extension">Extensión telefónica</label>
                      <input
                        id="pf-extension"
                        name="extension_telefonica"
                        value={form.extension_telefonica}
                        onChange={change}
                        placeholder="Ej. +57"
                      />
                    </div>

                    <div className="dp-field">
                      <label htmlFor="pf-nacimiento">Fecha de nacimiento *</label>
                      <input
                        id="pf-nacimiento"
                        type="date"
                        name="fecha_nacimiento"
                        value={form.fecha_nacimiento}
                        onChange={change}
                        required
                      />
                    </div>

                    <div className="dp-field">
                      <label htmlFor="pf-tipo-doc">Tipo de documento</label>
                      <select
                        id="pf-tipo-doc"
                        name="tipo_documento"
                        value={form.tipo_documento}
                        disabled
                      >
                        <option>CC</option>
                        <option>CE</option>
                        <option>NIT</option>
                        <option>TI</option>
                      </select>
                    </div>

                    <div className="dp-field">
                      <label htmlFor="pf-num-doc">Número de documento</label>
                      <input
                        id="pf-num-doc"
                        name="numero_documento"
                        value={form.numero_documento}
                        onChange={change}
                        disabled
                        required
                      />
                    </div>
                  </div>

                  {/* Sección: Dirección de entrega */}
                  <div className="dp-section-head">
                    <h2>Dirección de entrega</h2>
                  </div>

                  <div className="dp-grid-address">
                    <div className="dp-field">
                      <label htmlFor="pf-direccion">Dirección principal</label>
                      <input
                        id="pf-direccion"
                        name="direccion_residencia"
                        value={form.direccion_residencia}
                        onChange={change}
                        placeholder="Ej. Calle 85 # 12-34, apto. 402"
                      />
                    </div>

                    <div className="dp-field">
                      <label htmlFor="pf-referencia">Referencia de dirección</label>
                      <input
                        id="pf-referencia"
                        name="referencia_direccion"
                        value={form.referencia_direccion}
                        onChange={change}
                        placeholder="Torre, portería o punto cercano"
                      />
                    </div>

                    <div className="dp-field">
                      <label htmlFor="pf-latitud">Latitud</label>
                      <input
                        id="pf-latitud"
                        type="number"
                        step="0.000001"
                        name="latitud"
                        value={form.latitud ?? ''}
                        onChange={change}
                        placeholder="Opcional"
                      />
                    </div>

                    <div className="dp-field">
                      <label htmlFor="pf-longitud">Longitud</label>
                      <input
                        id="pf-longitud"
                        type="number"
                        step="0.000001"
                        name="longitud"
                        value={form.longitud ?? ''}
                        onChange={change}
                        placeholder="Opcional"
                      />
                    </div>
                  </div>
                </form>

                {/* Bloque de Seguridad de la cuenta */}
                <div className="dp-security-box">
                  <div className="dp-security-row">
                    <div className="dp-security-info">
                      <div className="dp-security-icon" aria-hidden="true">🔒</div>
                      <div>
                        <p className="dp-security-title">Seguridad de la cuenta</p>
                        <p className="dp-security-desc">
                          Puedes actualizar tu contraseña cuando lo necesites.
                        </p>
                      </div>
                    </div>

                    <button
                      type="button"
                      className="dp-security-trigger"
                      aria-expanded={showPasswordPanel}
                      onClick={() => {
                        setShowPasswordPanel(prev => !prev)
                        setPasswordError('')
                        setPasswordSuccess('')
                      }}
                    >
                      {showPasswordPanel ? 'Cerrar' : 'Cambiar contraseña'}
                    </button>
                  </div>

                  {passwordSuccess && (
                    <div className="account-success" role="status" style={{ marginTop: '0.85rem' }}>
                      ✓ <span>{passwordSuccess}</span>
                    </div>
                  )}

                  {showPasswordPanel && (
                    <form className="dp-password-drawer" onSubmit={guardarPassword}>
                      {passwordError && (
                        <p className="account-error" role="alert" style={{ marginBottom: '0.75rem' }}>
                          {passwordError}
                        </p>
                      )}

                      <div className="dp-password-grid">
                        <div className="dp-field">
                          <label htmlFor="pw-current">Contraseña actual *</label>
                          <input
                            id="pw-current"
                            type={showPasswords ? 'text' : 'password'}
                            name="current_password"
                            value={passwordForm.current_password}
                            onChange={changePassword}
                            autoComplete="current-password"
                            required
                          />
                        </div>

                        <div className="dp-field">
                          <label htmlFor="pw-new">Nueva contraseña *</label>
                          <input
                            id="pw-new"
                            type={showPasswords ? 'text' : 'password'}
                            name="new_password"
                            value={passwordForm.new_password}
                            onChange={changePassword}
                            autoComplete="new-password"
                            minLength={8}
                            required
                          />
                        </div>

                        <div className="dp-field">
                          <label htmlFor="pw-confirm">Confirmar contraseña *</label>
                          <input
                            id="pw-confirm"
                            type={showPasswords ? 'text' : 'password'}
                            name="confirm_password"
                            value={passwordForm.confirm_password}
                            onChange={changePassword}
                            autoComplete="new-password"
                            minLength={8}
                            required
                          />
                        </div>
                      </div>

                      <div className="dp-password-footer">
                        <button
                          type="button"
                          className="inline-link"
                          aria-pressed={showPasswords}
                          onClick={() => setShowPasswords(v => !v)}
                        >
                          {showPasswords ? 'Ocultar contraseñas' : 'Mostrar contraseñas'}
                        </button>

                        <button
                          type="submit"
                          className="dp-btn-save"
                          style={{ minWidth: '185px', height: '40px' }}
                          disabled={changingPassword}
                        >
                          {changingPassword ? 'Actualizando…' : 'Actualizar contraseña'}
                        </button>
                      </div>
                    </form>
                  )}
                </div>

                {/* Fila inferior de acciones */}
                <div className="dp-actions-row">
                  <button type="button" className="dp-btn-cancel" onClick={onBack}>
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    form="profile-edit-form"
                    className="dp-btn-save"
                    disabled={saving}
                  >
                    <span>{saving ? 'Guardando…' : 'Guardar cambios'}</span>
                    <span aria-hidden="true">→</span>
                  </button>
                </div>
              </>
            )}
          </div>

          <p className="dp-protected-note">
            <span aria-hidden="true">🔒</span>
            <span>Tus datos, siempre protegidos.</span>
          </p>
        </div>
      </main>
    </section>
  )
}