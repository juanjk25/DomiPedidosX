import { useEffect, useState } from 'react'
import { api } from '../api.js'

export default function CategoriaForm({ category, branches, branchId, onSaved, onCancel }) {
  const initialBranch = category?.sede ?? branchId ?? branches[0]?.id_sede ?? ''
  const [form, setForm] = useState({
    nombre: category?.nombre ?? '',
    descripcion: category?.descripcion ?? '',
    sede: initialBranch,
    activo: category?.activo ?? true,
  })
  const [errors, setErrors] = useState({})
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!form.sede && (branchId || branches[0]?.id_sede)) {
      setForm(current => ({
        ...current,
        sede: branchId || String(branches[0]?.id_sede || ''),
      }))
    }
  }, [branchId, branches, form.sede])

  function update(event) {
    const { name, value, type, checked } = event.target
    setForm(current => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
    setErrors(current => ({ ...current, [name]: '' }))
  }

  async function submit(event) {
    event.preventDefault()
    if (busy) return
    const nextErrors = {}
    if (!form.nombre.trim()) nextErrors.nombre = 'El nombre de la categoría es obligatorio.'
    if (!form.descripcion.trim()) nextErrors.descripcion = 'La descripción de la categoría es obligatoria.'
    if (!form.sede) nextErrors.sede = 'Selecciona una sede.'
    setErrors(nextErrors)
    setError('')
    if (Object.keys(nextErrors).length) {
      setError('Revisa los campos obligatorios.')
      return
    }

    setBusy(true)
    try {
      const savedCategory = await api(
        category ? `/management/categories/${category.id}/` : '/management/categories/',
        {
          method: category ? 'PATCH' : 'POST',
          body: JSON.stringify({
            nombre: form.nombre.trim(),
            descripcion: form.descripcion.trim(),
            sede: Number(form.sede),
            activo: form.activo,
          }),
        },
      )
      onSaved(
        savedCategory,
        category
          ? 'Los cambios de la categoría se guardaron correctamente.'
          : 'Categoría creada correctamente.',
      )
    } catch (err) {
      setError(err.message)
      setErrors(err.fields || {})
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="product-editor" aria-labelledby="category-editor-title">
      <div className="editor-heading">
        <div>
          <span className="login-kicker">{category ? 'EDITAR CATEGORÍA' : 'NUEVA CATEGORÍA'}</span>
          <h2 id="category-editor-title">{category ? category.nombre : 'Organiza tus productos'}</h2>
        </div>
        <button type="button" className="secondary-button" onClick={onCancel} disabled={busy}>
          Volver al listado
        </button>
      </div>
      <form onSubmit={submit} noValidate aria-busy={busy}>
        <fieldset disabled={busy}>
          <legend className="sr-only">Datos de la categoría</legend>
          <div className="product-fields">
            <label>
              Nombre *
              <input
                name="nombre"
                value={form.nombre}
                onChange={update}
                maxLength={50}
                required
                aria-invalid={!!errors.nombre}
              />
              {errors.nombre && <small className="field-error">{errors.nombre}</small>}
            </label>
            <label>
              Sede *
              <select
                name="sede"
                value={form.sede}
                onChange={update}
                required
                disabled={!!category?.sede || branches.length === 1}
                aria-invalid={!!errors.sede}
              >
                <option value="">Selecciona una sede</option>
                {branches.map(branch => (
                  <option key={branch.id_sede} value={branch.id_sede}>
                    {branch.nombre_sede}
                  </option>
                ))}
              </select>
              {errors.sede && <small className="field-error">{errors.sede}</small>}
            </label>
            <label className="category-description-field">
              Descripción *
              <textarea
                name="descripcion"
                value={form.descripcion}
                onChange={update}
                maxLength={500}
                required
                aria-invalid={!!errors.descripcion}
              />
              {errors.descripcion && <small className="field-error">{errors.descripcion}</small>}
            </label>
          </div>
          <label className="checkbox-label">
            <input type="checkbox" name="activo" checked={form.activo} onChange={update} />
            Categoría activa
          </label>
          {!form.activo && (
            <p className="field-error">
              Al desactivar esta categoría, todos sus productos se desactivarán.
            </p>
          )}
          {error && <p className="error-message" role="alert">{error}</p>}
          <div className="form-actions">
            <button className="secondary-button" type="button" onClick={onCancel}>
              Cancelar
            </button>
            <button type="submit" className="primary-button">
              {busy ? 'Guardando…' : category ? 'Guardar cambios' : 'Crear categoría'}
            </button>
          </div>
        </fieldset>
      </form>
    </section>
  )
}