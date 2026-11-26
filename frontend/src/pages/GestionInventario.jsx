import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'

const emptyForm = {
  sede: '',
  producto: '',
  cantidad_disponible: '0',
  stock_minimo: '10',
  stock_maximo: '100',
  activo: true,
}

export default function GestionInventario({
  user,
  onOpenMenu,
  onOpenOperator,
  onOpenTeam,
  onPreview,
  onLogout,
}) {
  const isAdmin = user?.role === 'admin'

  const [items, setItems] = useState([])
  const [branches, setBranches] = useState([])
  const [products, setProducts] = useState([])

  // Filtros conectados a query params del backend
  const [branch, setBranch] = useState('')
  const [search, setSearch] = useState('')
  const [activoFilter, setActivoFilter] = useState('all')
  const [stockBajoFilter, setStockBajoFilter] = useState('all')

  // Estado UI
  const [loading, setLoading] = useState(true)
  const [metadataLoading, setMetadataLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [revision, setRevision] = useState(0)

  // Modal crear / editar
  const [showModal, setShowModal] = useState(false)
  const [editingItem, setEditingItem] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  // Modal confirmación deshabilitar
  const [disableTarget, setDisableTarget] = useState(null)
  const [busyId, setBusyId] = useState(null)

  // 1. Cargar sedes permitidas
  useEffect(() => {
    const controller = new AbortController()
    setMetadataLoading(true)
    api('/management/branches/', { signal: controller.signal })
      .then(data => {
        const list = Array.isArray(data) ? data : []
        setBranches(list)
        if (!isAdmin && list.length > 0) {
          setBranch(String(list[0].id_sede))
        }
      })
      .catch(err => {
        if (err.name !== 'AbortError') setError(err.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setMetadataLoading(false)
      })
    return () => controller.abort()
  }, [isAdmin])

  // 2. Cargar productos activos de la sede al abrir el modal (crear o editar)
  const formBranchId = form.sede || branch || String(branches[0]?.id_sede || '')
  useEffect(() => {
    if (!showModal || !formBranchId) return
    const controller = new AbortController()
    api(`/management/products/?sede=${formBranchId}`, { signal: controller.signal })
      .then(data => {
        const activeProducts = (Array.isArray(data) ? data : []).filter(p => p.activo)
        setProducts(activeProducts)
      })
      .catch(err => {
        if (err.name !== 'AbortError') setFormError(err.message)
      })
    return () => controller.abort()
  }, [showModal, formBranchId])

  // Mantener el producto actual en las opciones aunque estuviera inactivo
  const productOptions = useMemo(() => {
    if (!editingItem) return products
    const exists = products.some(
      p => String(p.id_producto) === String(editingItem.producto)
    )
    if (exists) return products
    return [
      {
        id_producto: editingItem.producto,
        nombre_producto: editingItem.producto_nombre,
        codigo_de_barras: editingItem.codigo_de_barras,
      },
      ...products,
    ]
  }, [products, editingItem])

  const selectedProduct = useMemo(
    () => productOptions.find(p => String(p.id_producto) === String(form.producto)),
    [productOptions, form.producto]
  )

  // 3. Cargar inventario
  const loadInventory = useCallback(
    signal => {
      const params = new URLSearchParams()
      if (isAdmin && branch) params.set('sede', branch)
      if (activoFilter !== 'all') params.set('activo', activoFilter)
      if (stockBajoFilter !== 'all') params.set('stock_bajo', stockBajoFilter)
      if (search.trim()) params.set('search', search.trim())

      const qs = params.toString()
      return api(`/management/inventory/${qs ? `?${qs}` : ''}`, { signal })
    },
    [isAdmin, branch, activoFilter, stockBajoFilter, search]
  )

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError('')
    loadInventory(controller.signal)
      .then(data => setItems(Array.isArray(data) ? data : []))
      .catch(err => {
        if (err.name !== 'AbortError') setError(err.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [loadInventory, revision])

  // Cerrar modales con tecla Escape
  useEffect(() => {
    if (!showModal && !disableTarget) return
    const onKeyDown = e => {
      if (e.key === 'Escape') {
        if (showModal && !saving) closeModal()
        if (disableTarget && !busyId) setDisableTarget(null)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [showModal, disableTarget, saving, busyId])

  const stats = useMemo(() => {
    const active = items.filter(i => i.activo).length
    const lowStock = items.filter(i => i.activo && i.stock_bajo).length
    const inactive = items.filter(i => !i.activo).length
    return { total: items.length, active, lowStock, inactive }
  }, [items])

  function openCreateModal() {
    const defaultSede = branch || String(branches[0]?.id_sede || '')
    setEditingItem(null)
    setForm({ ...emptyForm, sede: defaultSede })
    setFormError('')
    setNotice('')
    setShowModal(true)
  }

  function openEditModal(item) {
    setEditingItem(item)
    setForm({
      sede: String(item.sede),
      producto: String(item.producto),
      cantidad_disponible: String(item.cantidad_disponible),
      stock_minimo: String(item.stock_minimo),
      stock_maximo: String(item.stock_maximo),
      activo: Boolean(item.activo),
    })
    setFormError('')
    setNotice('')
    setShowModal(true)
  }

  function closeModal() {
    setShowModal(false)
    setEditingItem(null)
    setFormError('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (saving) return

    const cantidad = Number(form.cantidad_disponible)
    const minimo = Number(form.stock_minimo)
    const maximo = Number(form.stock_maximo)

    if (!form.producto) {
      setFormError('Selecciona un producto.')
      return
    }
    if (Number.isNaN(cantidad) || cantidad < 0) {
      setFormError('La cantidad disponible debe ser un número mayor o igual a 0.')
      return
    }
    if (Number.isNaN(minimo) || minimo < 0) {
      setFormError('El stock mínimo debe ser un número mayor o igual a 0.')
      return
    }
    if (Number.isNaN(maximo) || maximo < 1) {
      setFormError('El stock máximo debe ser al menos 1.')
      return
    }
    if (minimo > maximo) {
      setFormError('El stock mínimo no puede ser mayor que el stock máximo.')
      return
    }
    if (cantidad > maximo) {
      setFormError('La cantidad disponible no puede superar el stock máximo.')
      return
    }

    setSaving(true)
    setFormError('')
    setError('')

    try {
      if (editingItem) {
        await api(`/management/inventory/${editingItem.id_inventario}/`, {
          method: 'PATCH',
          body: JSON.stringify({
            producto: Number(form.producto),
            cantidad_disponible: cantidad,
            stock_minimo: minimo,
            stock_maximo: maximo,
            activo: form.activo,
          }),
        })
        setNotice('Registro de inventario actualizado correctamente.')
      } else {
        const payload = {
          producto: Number(form.producto),
          cantidad_disponible: cantidad,
          stock_minimo: minimo,
          stock_maximo: maximo,
        }
        if (isAdmin) {
          if (!form.sede) {
            setFormError('Selecciona una sede.')
            setSaving(false)
            return
          }
          payload.sede = Number(form.sede)
        }
        await api('/management/inventory/', {
          method: 'POST',
          body: JSON.stringify(payload),
        })
        setNotice('Registro de inventario creado correctamente.')
      }

      closeModal()
      setRevision(r => r + 1)
    } catch (err) {
      setFormError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function confirmDisable() {
    if (!disableTarget || busyId) return
    setBusyId(disableTarget.id_inventario)
    setError('')
    setNotice('')
    try {
      const res = await api(`/management/inventory/${disableTarget.id_inventario}/disable/`, {
        method: 'PATCH',
      })
      setDisableTarget(null)
      setNotice(res?.message || 'Registro de inventario deshabilitado correctamente.')
      setRevision(r => r + 1)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  async function reactivateItem(item) {
    if (busyId) return
    setBusyId(item.id_inventario)
    setError('')
    setNotice('')
    try {
      await api(`/management/inventory/${item.id_inventario}/`, {
        method: 'PATCH',
        body: JSON.stringify({ activo: true }),
      })
      setNotice(`Inventario de "${item.producto_nombre}" reactivado correctamente.`)
      setRevision(r => r + 1)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <section className="management-page">
      <header className="management-header">
        <div className="menu-sidebar-brand">
          <span className="brand-mark">D</span>DomiPedidos<span className="brand-x">X</span>
        </div>
        <nav aria-label="Menú de gestión">
          {onOpenMenu && <button onClick={onOpenMenu}>Gestionar menú</button>}
          {onOpenOperator && <button onClick={onOpenOperator}>Panel operador</button>}
          {onOpenTeam && <button onClick={onOpenTeam}>Gestionar personal</button>}
          {onPreview && <button onClick={onPreview}>Ver menú del cliente</button>}
          <button onClick={onLogout}>Cerrar sesión</button>
        </nav>
      </header>

      <main className="management-main">
        <div className="management-title">
          <div>
            <span className="login-kicker">OPERACIÓN DE SEDE</span>
            <h1>Gestión de inventario</h1>
            <p>Controla existencias, niveles mínimos y disponibilidad por sede.</p>
          </div>
          <button
            type="button"
            className="primary-button"
            disabled={metadataLoading || branches.length === 0}
            onClick={openCreateModal}
          >
            ＋ Registrar inventario
          </button>
        </div>

        {notice && (
          <p className="status-message" role="status">
            {notice}
          </p>
        )}

        {error && (
          <p className="error-message" role="alert">
            {error}{' '}
            <button className="inline-link" onClick={() => setRevision(r => r + 1)}>
              Reintentar
            </button>
          </p>
        )}

        <div className="management-stats">
          <div>
            <strong>{stats.total}</strong>
            <span>Registros</span>
          </div>
          <div>
            <strong>{stats.active}</strong>
            <span>Activos</span>
          </div>
          <div>
            <strong>{stats.lowStock}</strong>
            <span>Stock bajo</span>
          </div>
          <div>
            <strong>{stats.inactive}</strong>
            <span>Deshabilitados</span>
          </div>
        </div>

        <div className="management-filters">
          {isAdmin && (
            <label>
              Sede
              <select value={branch} onChange={e => setBranch(e.target.value)}>
                <option value="">Todas las sedes</option>
                {branches.map(b => (
                  <option key={b.id_sede} value={b.id_sede}>
                    {b.nombre_sede}
                  </option>
                ))}
              </select>
            </label>
          )}

          <label>
            Buscar producto o código
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Nombre o código de barras"
            />
          </label>

          <label>
            Estado
            <select value={activoFilter} onChange={e => setActivoFilter(e.target.value)}>
              <option value="all">Todos</option>
              <option value="true">Activos</option>
              <option value="false">Deshabilitados</option>
            </select>
          </label>

          <label>
            Nivel de stock
            <select
              value={stockBajoFilter}
              onChange={e => setStockBajoFilter(e.target.value)}
            >
              <option value="all">Todos</option>
              <option value="true">Solo stock bajo</option>
              <option value="false">Stock normal</option>
            </select>
          </label>
        </div>

        {loading ? (
          <p role="status">Cargando inventario…</p>
        ) : !items.length ? (
          <div className="empty-state">
            <h2>No hay registros de inventario</h2>
            <p>Crea un nuevo registro o ajusta los filtros de búsqueda.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #ddd' }}>
                  <th style={{ padding: '0.75rem' }}>Producto</th>
                  <th style={{ padding: '0.75rem' }}>Sede</th>
                  <th style={{ padding: '0.75rem' }}>Disponible</th>
                  <th style={{ padding: '0.75rem' }}>Mín / Máx</th>
                  <th style={{ padding: '0.75rem' }}>Estado</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {items.map(item => (
                  <tr
                    key={item.id_inventario}
                    style={{
                      borderBottom: '1px solid #eee',
                      opacity: item.activo ? 1 : 0.65,
                    }}
                  >
                    <td style={{ padding: '0.75rem' }}>
                      <strong>{item.producto_nombre}</strong>
                      <div style={{ fontSize: '0.82rem', color: '#64748b' }}>
                        {item.tipo_de_producto || 'Sin categoría'} · Cód: {item.codigo_de_barras}
                      </div>
                    </td>
                    <td style={{ padding: '0.75rem' }}>{item.sede_nombre}</td>
                    <td style={{ padding: '0.75rem' }}>
                      <strong>{item.cantidad_disponible}</strong>
                      {item.activo && item.stock_bajo && (
                        <span
                          style={{
                            marginLeft: '0.5rem',
                            padding: '0.15rem 0.5rem',
                            borderRadius: '999px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            background: '#fef3c7',
                            color: '#92400e',
                          }}
                        >
                          Stock bajo
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      {item.stock_minimo} / {item.stock_maximo}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      <span className={`status-pill ${item.activo ? 'active' : 'inactive'}`}>
                        {item.activo ? 'Activo' : 'Deshabilitado'}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', whiteSpace: 'nowrap' }}>
                      <button
                        type="button"
                        className="secondary-button"
                        style={{ marginRight: '0.5rem' }}
                        onClick={() => openEditModal(item)}
                      >
                        Editar
                      </button>
                      {item.activo ? (
                        <button
                          type="button"
                          className="danger-link"
                          disabled={busyId === item.id_inventario}
                          onClick={() => setDisableTarget(item)}
                        >
                          Deshabilitar
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="secondary-button"
                          disabled={busyId === item.id_inventario}
                          onClick={() => reactivateItem(item)}
                        >
                          Reactivar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {/* Modal Crear / Editar inventario */}
      {showModal && (
        <div
          className="inv-modal-backdrop"
          role="presentation"
          onClick={e => {
            if (e.target === e.currentTarget && !saving) closeModal()
          }}
        >
          <div
            className="inv-modal-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="inv-modal-title"
          >
            <div className="inv-modal-header">
              <h2 id="inv-modal-title">
                {editingItem ? 'Editar inventario' : 'Registrar inventario'}
              </h2>
              <button
                type="button"
                className="inv-modal-close"
                aria-label="Cerrar"
                disabled={saving}
                onClick={closeModal}
              >
                ×
              </button>
            </div>

            {formError && (
              <p className="error-message" role="alert" style={{ marginBottom: '1rem' }}>
                {formError}
              </p>
            )}

            <form onSubmit={handleSubmit}>
              <div className="inv-modal-grid">
                <label className="inv-modal-field">
                  <span>PRODUCTO</span>
                  <select
                    value={form.producto}
                    onChange={e => setForm(old => ({ ...old, producto: e.target.value }))}
                    required
                  >
                    <option value="" disabled>
                      Selecciona un producto
                    </option>
                    {productOptions.map(p => (
                      <option key={p.id_producto} value={p.id_producto}>
                        {p.nombre_producto}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="inv-modal-field">
                  <span>SEDE</span>
                  {editingItem ? (
                    <input value={editingItem.sede_nombre} disabled />
                  ) : (
                    <select
                      value={form.sede}
                      disabled={!isAdmin}
                      onChange={e =>
                        setForm(old => ({ ...old, sede: e.target.value, producto: '' }))
                      }
                      required
                    >
                      <option value="" disabled>
                        Selecciona una sede
                      </option>
                      {branches.map(b => (
                        <option key={b.id_sede} value={b.id_sede}>
                          {b.nombre_sede}
                        </option>
                      ))}
                    </select>
                  )}
                </label>

                <label className="inv-modal-field">
                  <span>CANTIDAD DISPONIBLE</span>
                  <input
                    type="number"
                    min={0}
                    value={form.cantidad_disponible}
                    onChange={e =>
                      setForm(old => ({ ...old, cantidad_disponible: e.target.value }))
                    }
                    required
                  />
                </label>

                <label className="inv-modal-field">
                  <span>CÓDIGO DE BARRAS</span>
                  <input
                    value={selectedProduct?.codigo_de_barras || editingItem?.codigo_de_barras || '—'}
                    disabled
                  />
                </label>

                <label className="inv-modal-field">
                  <span>STOCK MÍNIMO</span>
                  <input
                    type="number"
                    min={0}
                    value={form.stock_minimo}
                    onChange={e => setForm(old => ({ ...old, stock_minimo: e.target.value }))}
                    required
                  />
                </label>

                <label className="inv-modal-field">
                  <span>STOCK MÁXIMO</span>
                  <input
                    type="number"
                    min={1}
                    value={form.stock_maximo}
                    onChange={e => setForm(old => ({ ...old, stock_maximo: e.target.value }))}
                    required
                  />
                </label>
              </div>

              {editingItem && (
                <label className="inv-modal-checkbox">
                  <input
                    type="checkbox"
                    checked={form.activo}
                    onChange={e => setForm(old => ({ ...old, activo: e.target.checked }))}
                  />
                  <span>Registro activo en el inventario</span>
                </label>
              )}

              <div className="inv-modal-actions">
                <button
                  type="button"
                  className="inv-btn-cancel"
                  disabled={saving}
                  onClick={closeModal}
                >
                  Cancelar
                </button>
                <button type="submit" className="inv-btn-save" disabled={saving}>
                  {saving
                    ? 'Guardando…'
                    : editingItem
                      ? 'Guardar cambios'
                      : 'Crear registro'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Confirmación Deshabilitar */}
      {disableTarget && (
        <div
          className="inv-modal-backdrop"
          role="presentation"
          onClick={e => {
            if (e.target === e.currentTarget && !busyId) setDisableTarget(null)
          }}
        >
          <div className="inv-modal-card inv-modal-card--sm" role="alertdialog" aria-modal="true">
            <div className="inv-modal-header">
              <h2>Deshabilitar inventario</h2>
              <button
                type="button"
                className="inv-modal-close"
                aria-label="Cerrar"
                disabled={!!busyId}
                onClick={() => setDisableTarget(null)}
              >
                ×
              </button>
            </div>
            <p style={{ margin: '0 0 1.5rem', color: '#475569', lineHeight: 1.5 }}>
              ¿Seguro que deseas deshabilitar el registro de{' '}
              <strong>{disableTarget.producto_nombre}</strong> en{' '}
              <strong>{disableTarget.sede_nombre}</strong>?
            </p>
            <div className="inv-modal-actions">
              <button
                type="button"
                className="inv-btn-cancel"
                disabled={!!busyId}
                onClick={() => setDisableTarget(null)}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="inv-btn-danger"
                disabled={busyId === disableTarget.id_inventario}
                onClick={confirmDisable}
              >
                {busyId === disableTarget.id_inventario
                  ? 'Deshabilitando…'
                  : 'Deshabilitar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}