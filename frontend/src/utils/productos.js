export function validateProduct(form) {
  const errors = {}
  for (const field of ['nombre_producto', 'codigo_de_barras', 'categoria', 'sede', 'imagen_url', 'tiempo_preparacion', 'precio_venta']) {
    if (!String(form[field] ?? '').trim()) errors[field] = 'Este campo es obligatorio.'
  }
  if (form.nombre_producto?.trim().length > 80) errors.nombre_producto = 'Máximo 80 caracteres.'
  if (form.codigo_de_barras?.trim().length > 30) errors.codigo_de_barras = 'Máximo 30 caracteres.'
  for (const [field, min] of [['precio_venta', 0.01], ['precio_compra', 0]]) {
    const value = String(form[field] ?? '')
    if (!/^\d+(\.\d{1,2})?$/.test(value) || Number(value) < min || Number(value) > 9999999999.99) {
      errors[field] = `Ingresa un valor desde ${min}, con máximo dos decimales.`
    }
  }
  const minutes = Number(form.tiempo_preparacion)
  if (!Number.isInteger(minutes) || minutes < 1 || minutes > 1440) errors.tiempo_preparacion = 'Ingresa de 1 a 1440 minutos enteros.'
  try {
    const url = new URL(form.imagen_url)
    if (!['http:', 'https:'].includes(url.protocol) || String(form.imagen_url).length > 500) throw new Error()
  } catch { errors.imagen_url = 'Ingresa una URL de imagen HTTP o HTTPS válida (máximo 500 caracteres).' }
  return errors
}
export function productPayload(form) {
  return { ...form, nombre_producto: form.nombre_producto.trim(), codigo_de_barras: form.codigo_de_barras.trim(), imagen_url: form.imagen_url.trim(), categoria: Number(form.categoria), sede: Number(form.sede), tiempo_preparacion: Number(form.tiempo_preparacion) }
}
export function visibleProducts(products, query = '', status = 'all') {
  const search = query.trim().toLocaleLowerCase('es')
  return products.filter(p => p.nombre_producto.toLocaleLowerCase('es').includes(search) && (status === 'all' || p.activo === (status === 'active')))
}
export function announceMenuChange() {
  localStorage.setItem('domi_menu_revision', `${Date.now()}-${Math.random()}`)
  window.dispatchEvent(new Event('domi:menu-updated'))
}
export const money = value => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(Number(value))
