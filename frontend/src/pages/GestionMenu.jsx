import { useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'
import ProductoForm from '../components/ProductoForm.jsx'
import ConfirmarDesactivacion from '../components/ConfirmarDesactivacion.jsx'
import ImagenProducto from '../components/ImagenProducto.jsx'
import { announceMenuChange, money, visibleProducts } from '../utils/productos.js'

export default function GestionMenu({ onPreview, onLogout }) {
  const [products, setProducts] = useState([]), [categories, setCategories] = useState([]), [branches, setBranches] = useState([])
  const [branch, setBranch] = useState(null), [query, setQuery] = useState(''), [status, setStatus] = useState('all')
  const [editor, setEditor] = useState(null), [target, setTarget] = useState(null), [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true), [error, setError] = useState(''), [actionError, setActionError] = useState(''), [notice, setNotice] = useState(''), [revision, setRevision] = useState(0)
  const [metadataError, setMetadataError] = useState('')
  useEffect(() => {
    const controller = new AbortController()
    setMetadataError('')
    Promise.all([api('/management/categories/', { signal: controller.signal }), api('/management/branches/', { signal: controller.signal })])
      .then(([c, b]) => { setCategories(c); setBranches(b); setBranch(old => old === null ? String(b[0]?.id_sede || '') : old) })
      .catch(e => { if (e.name !== 'AbortError') setMetadataError(e.message) })
    return () => controller.abort()
  }, [revision])
  useEffect(() => {
    const controller = new AbortController()
    setLoading(true); setError('')
    api(`/management/products/${branch ? `?sede=${branch}` : ''}`, { signal: controller.signal })
      .then(setProducts).catch(e => { if (e.name !== 'AbortError') setError(e.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [branch, revision])
  const filtered = useMemo(() => visibleProducts(products, query, status), [products, query, status])
  function saved(message) { setEditor(null); setNotice(message); setRevision(x => x + 1); announceMenuChange() }
  async function deactivate() {
    if (busy) return
    setBusy(true); setActionError('')
    try {
      await api(`/management/products/${target.id_producto}/`, { method: 'PATCH', body: JSON.stringify({ activo: false }) })
      setTarget(null); saved('Producto desactivado. Ya no aparece en el menú del cliente.')
    } catch (err) { setActionError(err.message) }
    finally { setBusy(false) }
  }
  return <section className="management-page">
    <header className="management-header"><div className="menu-sidebar-brand"><span className="brand-mark">D</span>DomiPedidos<span className="brand-x">X</span></div><nav aria-label="Menú de operador"><button onClick={onPreview}>Ver menú del cliente</button><button onClick={onLogout}>Cerrar sesión</button></nav></header>
    <main className="management-main"><div className="management-title"><div><span className="login-kicker">OPERACIÓN DE SEDE</span><h1>Gestionar menú</h1><p>Organiza tus productos y decide qué ve el cliente.</p></div>{!editor && <button className="primary-button" disabled={!branch || !!metadataError} onClick={() => { setNotice(''); setEditor({}) }}>＋ Crear producto</button>}</div>
      {notice && <p className="status-message" role="status">{notice}</p>}
      {(error || metadataError) && <p className="error-message" role="alert">{error || metadataError} <button className="inline-link" onClick={() => setRevision(x => x + 1)}>Reintentar</button></p>}
      {editor ? <ProductoForm key={editor.id_producto || 'new'} product={editor.id_producto ? editor : null} categories={categories} branches={branches} branchId={branch} onSaved={saved} onCancel={() => setEditor(null)} />
        : <>
          <div className="management-stats"><div><strong>{products.length}</strong><span>Productos</span></div><div><strong>{products.filter(p => p.activo).length}</strong><span>Activos</span></div><div><strong>{products.filter(p => !p.activo).length}</strong><span>Inactivos</span></div></div>
          <div className="management-filters"><label>Sede<select value={branch ?? ''} onChange={e => { setBranch(e.target.value); setNotice('') }}><option value="">Todas las sedes</option>{branches.map(b => <option key={b.id_sede} value={b.id_sede}>{b.nombre_sede}</option>)}</select></label><label>Buscar producto<input value={query} onChange={e => setQuery(e.target.value)} placeholder="Nombre del producto" /></label><label>Estado<select value={status} onChange={e => setStatus(e.target.value)}><option value="all">Todos</option><option value="active">Activos</option><option value="inactive">Inactivos</option></select></label></div>
          {loading ? <p role="status">Cargando productos…</p> : <>
            <p className="result-count">{filtered.length} productos encontrados</p>
            {!filtered.length && <div className="empty-state"><h2>No hay productos para mostrar</h2><p>Crea un producto o cambia los filtros.</p></div>}
            <div className="management-grid">{filtered.map(product => <article className="management-product" key={product.id_producto}>
              <div className="management-product-image"><ImagenProducto src={product.imagen_url} name={product.nombre_producto} /><span className={`status-pill ${product.activo ? 'active' : 'inactive'}`}>{product.activo ? 'Activo' : 'Inactivo'}</span></div>
              <div className="management-product-copy"><span className="product-category">{product.tipo_de_producto}</span><h2>{product.nombre_producto}</h2><p>{product.tiempo_preparacion ? `${product.tiempo_preparacion} min de preparación` : 'Completa el tiempo de preparación'}</p><strong>{money(product.precio_venta)}</strong>
                {!product.sede && <p className="field-error">Pendiente de asignación de sede.</p>}
                {categories.some(c => c.id === product.categoria && !c.activo) && <p className="field-error">Categoría inactiva: oculto al cliente.</p>}
                <div className="product-actions"><button className="secondary-button" onClick={() => { setNotice(''); setEditor(product) }}>Editar</button>{product.activo && <button className="danger-link" onClick={() => { setActionError(''); setTarget(product) }}>Desactivar</button>}</div>
              </div>
            </article>)}</div>
          </>}
        </>}
    </main>
    {target && <ConfirmarDesactivacion product={target} busy={busy} error={actionError} onConfirm={deactivate} onCancel={() => setTarget(null)} />}
  </section>
}
