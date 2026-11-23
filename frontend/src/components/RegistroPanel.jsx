import { useState } from 'react'
import RegistroCliente from '../pages/RegistroCliente.jsx'
import { api, clearSession, saveTokens } from '../api.js'

// Adaptador del formulario de Junior; conserva sus props y sus campos.
export default function RegistroPanel({ onAuthenticated, navigate }) {
  const [form, setForm] = useState({ email: '', password: '', first_name: '', last_name: '', phone: '', phone_extension: '', tipo_documento: 'CC', numero_documento: '', date_of_birth: '', delivery_address: '', address_reference: '' })
  const [error, setError] = useState(''), [busy, setBusy] = useState(false)
  const update = event => {
    const { name, value } = event.target
    setForm(current => ({ ...current, [name]: ['numero_documento', 'phone', 'phone_extension'].includes(name) ? value.replace(/\D/g, '') : value }))
  }
  async function submit(event) {
    event.preventDefault()
    if (busy) return
    setError(''); setBusy(true)
    try {
      const data = { email: form.email, password: form.password, nombres: form.first_name, apellidos: form.last_name, tipo_documento: form.tipo_documento, numero_documento: form.numero_documento, telefono_cliente: form.phone, extension_telefonica: form.phone_extension, direccion_residencia: form.delivery_address, referencia_direccion: form.address_reference, fecha_nacimiento: form.date_of_birth }
      const registered = await api('/auth/register/', { auth: false, method: 'POST', body: JSON.stringify(data) })
      const tokens = await api('/auth/token/', { auth: false, method: 'POST', body: JSON.stringify({ username: registered.username, password: form.password }) })
      saveTokens(tokens)
      await onAuthenticated()
    } catch (err) { clearSession(); setError(err.message) }
    finally { setBusy(false) }
  }
  return <RegistroCliente form={form} update={update} error={error} busy={busy} onSubmit={submit} onBackToLogin={() => navigate('/login')} />
}
