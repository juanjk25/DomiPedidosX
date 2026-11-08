import { useState } from 'react'

const RegistroCliente = ({ form, update, error, busy, onSubmit, onBackToLogin }) => {
  const [confirmPassword, setConfirmPassword] = useState('')
  const [validationError, setValidationError] = useState('')

  function handleSubmit(event) {
    event.preventDefault()
    if (form.password !== confirmPassword) {
      setValidationError('Las contraseñas no coinciden.')
      return
    }
    setValidationError('')
    onSubmit(event)
  }

  return <section className="registration-page">
    <div className="registration-layout">
      <aside className="registration-aside">
        <div className="registration-aside-content">
          <span className="registration-kicker">BIENVENIDO A DOMIPEDIDOSX</span>
          <h1>Tu pizza favorita,<br /><em>como tú la quieres.</em></h1>
          <p>Regístrate y disfruta de tus pedidos favoritos sin complicarte.</p>
        </div>
        <div className="registration-pizza" aria-hidden="true">
          <div className="pizza-plate"></div>
          <div className="pizza">
            <span>🍕</span>
          </div>
        </div>
        <span className="registration-aside-note">HECHO CERCA. LLEGA A TU PUERTA.</span>
      </aside>

      <div className="registration-form-panel">
        <div className="registration-heading">
          <span className="eyebrow">CREAR CUENTA</span>
          <h2>Tu cuenta, tu próxima pizza</h2>
          <p>Completa tus datos para empezar a pedir.</p>
        </div>

        <form className="registration-form" onSubmit={handleSubmit} autoComplete="off">
          <div className="registration-fields-row">
            <label>Nombre *
              <input name="first_name" value={form.first_name} onChange={update} placeholder="Tu nombre" required />
            </label>
            <label>Apellido *
              <input name="last_name" value={form.last_name} onChange={update} placeholder="Tu apellido" required />
            </label>
          </div>
          <div className="registration-fields-row">
            <label>Teléfono *
              <input name="phone" type="text" inputMode="numeric" pattern="[0-9]*" value={form.phone} onChange={update} placeholder="3000000000" autoComplete="off" required />
            </label>
            <label>Extensión telefónica <span className="optional">· Opcional</span>
              <input name="phone_extension" type="text" inputMode="numeric" pattern="[0-9]*" value={form.phone_extension} onChange={update} placeholder="Ej. 101" autoComplete="off" />
            </label>
          </div>
          <div className="registration-fields-row">
            <label>Tipo de documento *
              <select name="tipo_documento" value={form.tipo_documento} onChange={update} required>
                <option value="CC">Cédula de ciudadanía</option>
                <option value="CE">Cédula de extranjería</option>
                <option value="NIT">NIT</option>
                <option value="TI">Tarjeta de identidad</option>
              </select>
            </label>
            <label>Número de documento *
              <input name="numero_documento" type="text" inputMode="numeric" pattern="[0-9]*" value={form.numero_documento} onChange={update} placeholder="Número de documento" autoComplete="off" required />
            </label>
          </div>
          <label>Correo electrónico *
            <input type="email" name="email" value={form.email} onChange={update} placeholder="tucorreo@ejemplo.com" autoComplete="new-email" required />
          </label>
          <div className="registration-fields-row">
            <label>Contraseña *
              <input type="password" name="password" value={form.password} onChange={update} placeholder="Crea una contraseña" autoComplete="new-password" minLength="8" required />
            </label>
            <label>Confirmar contraseña *
              <input type="password" value={confirmPassword} onChange={event => setConfirmPassword(event.target.value)} placeholder="Repite tu contraseña" autoComplete="new-password" minLength="8" required />
            </label>
          </div>
          <label>Fecha de nacimiento *
            <input type="date" name="date_of_birth" value={form.date_of_birth} onChange={update} autoComplete="off" required />
          </label>
          <p className="field-hint">Documento, teléfono y extensión: escribe solo números.</p>
          <p className="field-hint">Mínimo 8 caracteres, una mayúscula y un número.</p>
          <div className="registration-address">
            <h3>¿Dónde te llevamos tu pizza?</h3>
            <p>Dirección georreferenciada obligatoria. Confirma el punto en el mapa.</p>
            <label>Buscar dirección *
              <input name="delivery_address" value={form.delivery_address} onChange={update} placeholder="Calle 85 # 15-20, Bogotá" autoComplete="street-address" required />
            </label>
            <div className="address-map" role="img" aria-label="Mapa para confirmar la ubicación de entrega">
              <span className="map-pin">●</span>
              <span className="map-label">Confirma tu ubicación</span>
            </div>
            <label>Referencia o complemento <span className="optional">· Opcional</span>
              <input name="address_reference" value={form.address_reference} onChange={update} placeholder="Apartamento, casa, punto de referencia..." />
            </label>
          </div>
          {(validationError || error) && <p className="error-message">{validationError || error}</p>}
          <label className="registration-terms">
            <input type="checkbox" required />
            <span>Acepto los términos y condiciones y la política de privacidad.</span>
          </label>
          <button className="button registration-submit" disabled={busy}>{busy ? 'Creando tu cuenta…' : 'Crear mi cuenta'} <span>→</span></button>
        </form>

        <p className="registration-login">¿Ya tienes una cuenta? <button type="button" onClick={onBackToLogin}>Inicia sesión</button></p>
        <p className="registration-security">🔒 Tus datos están protegidos y no compartimos tu información.</p>
      </div>
    </div>
  </section>
}

export default RegistroCliente
