import { useState } from 'react'
import { api } from '../api.js'
import { productPayload, validateProduct } from '../utils/productos.js'
import ImagenProducto from './ImagenProducto.jsx'

export default function ProductoForm({ product, categories, branches, branchId, onSaved, onCancel }) {
  const [form, setForm] = useState({
    nombre_producto: product?.nombre_producto ?? '', codigo_de_barras: product?.codigo_de_barras ?? '',
    precio_venta: product?.precio_venta ?? '', precio_compra: product?.precio_compra ?? '0',
    categoria: product?.categoria ?? '', sede: product?.sede ?? branchId,
    imagen_url: product?.imagen_url ?? '', tiempo_preparacion: product?.tiempo_preparacion ?? '', activo: product?.activo ?? true,
  })
  const [errors, setErrors] = useState({}), [error, setError] = useState(''), [busy, setBusy] = useState(false)
  const availableCategories = categories.filter(c => String(c.sede) === String(form.sede))
  const update = e => {
    const { name, value, type, checked } = e.target
    setForm(f => ({ ...f, [name]: type === 'checkbox' ? checked : value, ...(name === 'sede' ? { categoria: '' } : {}) }))
    setErrors(old => ({ ...old, [name]: '' }))
  }
  const field = (name, label, type = 'text', extra = {}) => <label>{label} *
    <input name={name} type={type} value={form[name]} onChange={update} required aria-invalid={!!errors[name]} aria-describedby={errors[name] ? `error-${name}` : undefined} {...extra} />
    {errors[name] && <small className="field-error" id={`error-${name}`}>{errors[name]}</small>}
  </label>
  async function submit(event) {
    event.preventDefault()
    if (busy) return
    const nextErrors = validateProduct(form)
    if (!availableCategories.some(c => String(c.id) === String(form.categoria) && c.activo)) nextErrors.categoria = 'Selecciona una categoría activa de esta sede.'
    setErrors(nextErrors); setError('')
    if (Object.keys(nextErrors).length) { setError('Revisa los campos marcados.'); return }
    setBusy(true)
    try {
      await api(product ? `/management/products/${product.id_producto}/` : '/management/products/', { method: product ? 'PATCH' : 'POST', body: JSON.stringify(productPayload(form)) })
      onSaved(product ? 'Producto actualizado.' : 'Producto creado y asociado a la sede.')
    } catch (err) { setError(err.message); setErrors(err.fields || {}); setBusy(false) }
  }
  return <section className="product-editor" aria-labelledby="editor-title">
    <div className="editor-heading"><div><span className="login-kicker">{product ? 'EDITAR PRODUCTO' : 'NUEVO PRODUCTO'}</span><h2 id="editor-title">{product ? product.nombre_producto : 'Agrega algo al menú'}</h2></div><button className="secondary-button" onClick={onCancel} disabled={busy}>Volver al listado</button></div>
    <form onSubmit={submit} noValidate aria-busy={busy}>
      <fieldset disabled={busy}><legend className="sr-only">Datos del producto</legend>
        <div className="product-fields">
          {field('nombre_producto', 'Nombre del producto', 'text', { maxLength: 80 })}
          {field('codigo_de_barras', 'Código de barras o código interno', 'text', { maxLength: 30 })}
          {field('precio_venta', 'Precio de venta (COP)', 'number', { min: '0.01', max: '9999999999.99', step: '0.01' })}
          <label>Precio de compra (COP)<input type="number" name="precio_compra" min="0" step="0.01" value={form.precio_compra} onChange={update} aria-invalid={!!errors.precio_compra} />{errors.precio_compra && <small className="field-error">{errors.precio_compra}</small>}</label>
          <label>Categoría *<select name="categoria" value={form.categoria} onChange={update} required aria-invalid={!!errors.categoria}><option value="">Selecciona una categoría</option>{availableCategories.map(c => <option key={c.id} value={c.id} disabled={!c.activo}>{c.nombre}{!c.activo ? ' (inactiva)' : ''}</option>)}</select>{errors.categoria && <small className="field-error">{errors.categoria}</small>}</label>
          <label>Sede *<select name="sede" value={form.sede} onChange={update} required disabled={!!product?.sede || branches.length === 1} aria-invalid={!!errors.sede}><option value="">Selecciona una sede</option>{branches.map(b => <option key={b.id_sede} value={b.id_sede}>{b.nombre_sede}</option>)}</select>{errors.sede && <small className="field-error">{errors.sede}</small>}</label>
          {field('tiempo_preparacion', 'Tiempo de preparación (minutos)', 'number', { min: 1, max: 1440, step: 1 })}
          {field('imagen_url', 'URL de la imagen', 'url', { maxLength: 500, placeholder: 'https://ejemplo.com/producto.jpg' })}
        </div>
        <div className="product-preview"><ImagenProducto src={/^https?:\/\//.test(form.imagen_url) ? form.imagen_url : ''} name={form.nombre_producto || 'Producto'} /><p>Usa un enlace directo a una imagen accesible. Si no carga, se mostrará una imagen de reemplazo.</p></div>
        <label className="checkbox-label"><input type="checkbox" name="activo" checked={form.activo} onChange={update} />Publicado en el menú del cliente</label>
        {!availableCategories.some(c => c.activo) && <p className="error-message">No hay categorías activas. Deben crearse antes de guardar un producto.</p>}
        {error && <p className="error-message" role="alert">{error}</p>}
        <div className="form-actions"><button className="secondary-button" type="button" onClick={onCancel}>Cancelar</button><button className="primary-button" disabled={!availableCategories.some(c => c.activo)}>{busy ? 'Guardando…' : product ? 'Guardar cambios' : 'Crear producto'}</button></div>
      </fieldset>
    </form>
  </section>
}
