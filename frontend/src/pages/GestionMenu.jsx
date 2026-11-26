import { useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'
import ProductoForm from '../components/ProductoForm.jsx'
import ConfirmarDesactivacion from '../components/ConfirmarDesactivacion.jsx'
import ImagenProducto from '../components/ImagenProducto.jsx'
import CategoriaForm from '../components/CategoriaForm.jsx'
import { announceMenuChange, money, visibleProducts } from '../utils/productos.js'

export default function GestionMenu({ onPreview, onOpenTeam, onLogout }) {
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [branches, setBranches] = useState([])
  const [branch, setBranch] = useState(null)
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('all')
  const [editor, setEditor] = useState(null)
  const [target, setTarget] = useState(null)
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [notice, setNotice] = useState('')
  const [revision, setRevision] = useState(0)
  const [metadataLoading, setMetadataLoading] = useState(true)
  const [metadataError, setMetadataError] = useState('')
  const [categoryEditor, setCategoryEditor] = useState(null)
  const [categoryTarget, setCategoryTarget] = useState(null)
  const [categoryBusy, setCategoryBusy] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    setMetadataLoading(true)
    setMetadataError('')
    Promise.all([
      api('/management/categories/', { signal: controller.signal }),
      api('/management/branches/', { signal: controller.signal }),
    ])
      .then(([c, b]) => {
        setCategories(c)
        setBranches(b)
        setBranch(old => (old === null ? String(b[0]?.id_sede || '') : old))
      })
      .catch(e => {
        if (e.name !== 'AbortError') setMetadataError(e.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setMetadataLoading(false)
      })
    return () => controller.abort()
  }, [revision])

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError('')
    api(`/management/products/${branch ? `?sede=${branch}` : ''}`, { signal: controller.signal })
      .then(setProducts)
      .catch(e => {
        if (e.name !== 'AbortError') setError(e.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [branch, revision])

  const filtered = useMemo(() => visibleProducts(products, query, status), [products, query, status])
  const defaultBranchId = branch || String(branches[0]?.id_sede || '')
  const canCreate = !metadataLoading && !metadataError && branches.length > 0

  function saved(message) {
    setEditor(null)
    setNotice(message)
    setRevision(x => x + 1)
    announceMenuChange()
  }

  function categorySaved(savedCategory, message) {
    setCategories(old =>
      savedCategory?.id
        ? old.some(category => category.id === savedCategory.id)
          ? old.map(category => (category.id === savedCategory.id ? savedCategory : category))
          : [...old, savedCategory]
        : old
    )
    setCategoryEditor(null)
    setNotice(message)
    setRevision(x => x + 1)
    announceMenuChange()
  }

  async function deactivate() {
    if (busy) return
    setBusy(true)
    setActionError('')
    try {
      await api(`/management/products/${target.id_producto}/`, {
        method: 'PATCH',
        body: JSON.stringify({ activo: false }),
      })
      setTarget(null)
      saved('Producto desactivado. Ya no aparece en el menú del cliente.')
    } catch (err) {
      setActionError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function deleteCategory() {
    if (categoryBusy) return
    setCategoryBusy(true)
    setActionError('')
    try {
      await api(`/management/categories/${categoryTarget.id}/`, { method: 'DELETE' })
      setCategoryTarget(null)
      setCategoryBusy(false)
      saved('Categoría eliminada.')
    } catch (err) {
      setActionError(err.message)
      setCategoryBusy(false)
    }
  }

  return (
    <section className="management-page">
      <header className="management-header">
        <div className="menu-sidebar-brand">
          <span className="brand-mark">D</span>DomiPedidos<span className="brand-x">X</span>
        </div>
        <nav aria-label="Menú de operador">
          {onOpenTeam && <button onClick={onOpenTeam}>Gestionar personal</button>}
          <button onClick={onPreview}>Ver menú del cliente</button>
          <button onClick={onLogout}>Cerrar sesión</button>
        </nav>
      </header>

      <main className="management-main">
        <div className="management-title">
          <div>
            <span className="login-kicker">OPERACIÓN DE SEDE</span>
            <h1>Gestionar menú</h1>
            <p>Organiza tus categorías y productos.</p>
          </div>
          {!editor && !categoryEditor && (
            <div className="management-create-actions">
              <button
                type="button"
                className="secondary-button"
                disabled={!canCreate}
                onClick={() => {
                  setNotice('')
                  setCategoryEditor({})
                }}
              >
                ＋ Crear categoría
              </button>
              <button
                type="button"
                className="primary-button"
                disabled={!canCreate}
                onClick={() => {
                  setNotice('')
                  setEditor({})
                }}
              >
                ＋ Crear producto
              </button>
            </div>
          )}
        </div>

        {notice && (
          <p className="status-message" role="status">
            {notice}
          </p>
        )}

        {(error || metadataError) && (
          <p className="error-message" role="alert">
            {error || metadataError}{' '}
            <button className="inline-link" onClick={() => setRevision(x => x + 1)}>
              Reintentar
            </button>
          </p>
        )}

        {!metadataLoading && !metadataError && branches.length === 0 && (
          <p className="error-message" role="alert">
            No hay sedes disponibles para tu cuenta. Verifica que exista al menos una sede registrada o asignada a tu perfil para crear categorías y productos.
          </p>
        )}

        {categoryEditor ? (
          <CategoriaForm
            key={categoryEditor.id || 'new-category'}
            category={categoryEditor.id ? categoryEditor : null}
            branches={branches}
            branchId={defaultBranchId}
            onSaved={categorySaved}
            onCancel={() => setCategoryEditor(null)}
          />
        ) : editor ? (
          <ProductoForm
            key={editor.id_producto || 'new'}
            product={editor.id_producto ? editor : null}
            categories={categories}
            branches={branches}
            branchId={defaultBranchId}
            onSaved={saved}
            onCancel={() => setEditor(null)}
          />
        ) : (
          <>
            <div className="management-stats">
              <div>
                <strong>{products.length}</strong>
                <span>Productos</span>
              </div>
              <div>
                <strong>{products.filter(p => p.activo).length}</strong>
                <span>Activos</span>
              </div>
              <div>
                <strong>{products.filter(p => !p.activo).length}</strong>
                <span>Inactivos</span>
              </div>
            </div>

            <div className="management-filters">
              <label>
                Sede
                <select
                  value={branch ?? ''}
                  onChange={e => {
                    setBranch(e.target.value)
                    setNotice('')
                  }}
                >
                  <option value="">Todas las sedes</option>
                  {branches.map(b => (
                    <option key={b.id_sede} value={b.id_sede}>
                      {b.nombre_sede}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Buscar producto
                <input
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Nombre del producto"
                />
              </label>
              <label>
                Estado
                <select value={status} onChange={e => setStatus(e.target.value)}>
                  <option value="all">Todos</option>
                  <option value="active">Activos</option>
                  <option value="inactive">Inactivos</option>
                </select>
              </label>
            </div>

            <section className="category-management" aria-labelledby="category-management-title">
              <div className="category-management-heading">
                <div>
                  <span className="login-kicker">CATEGORÍAS</span>
                  <h2 id="category-management-title">Organiza tus productos</h2>
                </div>
              </div>
              <div className="category-management-grid">
                {categories
                  .filter(category => !branch || String(category.sede) === String(branch))
                  .map(category => {
                    const productCount = products.filter(
                      product => String(product.categoria) === String(category.id)
                    ).length
                    return (
                      <article className="category-card" key={category.id}>
                        <div className="category-card-heading">
                          <div>
                            <h3>{category.nombre}</h3>
                            <span className={`status-pill ${category.activo ? 'active' : 'inactive'}`}>
                              {category.activo ? 'Activa' : 'Inactiva'}
                            </span>
                          </div>
                          <strong>
                            {productCount} {productCount === 1 ? 'producto' : 'productos'}
                          </strong>
                        </div>
                        <p>{category.descripcion || 'Sin descripción.'}</p>
                        <div className="product-actions">
                          <button
                            className="secondary-button"
                            onClick={() => {
                              setNotice('')
                              setCategoryEditor(category)
                            }}
                          >
                            Editar
                          </button>
                          <button
                            className="danger-link"
                            onClick={() => {
                              setActionError('')
                              setCategoryTarget(category)
                            }}
                          >
                            Eliminar
                          </button>
                        </div>
                      </article>
                    )
                  })}
                {!categories.filter(category => !branch || String(category.sede) === String(branch))
                  .length && (
                  <div className="category-empty">
                    No hay categorías en esta sede. Crea la primera.
                  </div>
                )}
              </div>
            </section>

            {loading ? (
              <p role="status">Cargando productos…</p>
            ) : (
              <>
                <p className="result-count">{filtered.length} productos encontrados</p>
                {!filtered.length && (
                  <div className="empty-state">
                    <h2>No hay productos para mostrar</h2>
                    <p>Crea un producto o cambia los filtros.</p>
                  </div>
                )}
                <div className="management-grid">
                  {filtered.map(product => {
                    const productCategory = categories.find(
                      c => String(c.id) === String(product.categoria)
                    )
                    const productBranch = branches.find(
                      b => String(b.id_sede) === String(product.sede)
                    )
                    const summaryText =
                      productCategory?.descripcion?.trim() ||
                      `Código: ${product.codigo_de_barras}${productBranch ? ` · ${productBranch.nombre_sede}` : ''}`

                    return (
                      <article className="management-product" key={product.id_producto}>
                        <div className="management-product-image">
                          <ImagenProducto src={product.imagen_url} name={product.nombre_producto} />
                          <span className={`status-pill ${product.activo ? 'active' : 'inactive'}`}>
                            {product.activo ? 'Activo' : 'Inactivo'}
                          </span>
                        </div>
                        <div className="management-product-copy">
                          <span className="product-category">
                            {product.tipo_de_producto || 'Sin categoría'}
                          </span>
                          <h2 title={product.nombre_producto}>{product.nombre_producto}</h2>
                          <p className="product-description" title={summaryText}>
                            {summaryText}
                          </p>
                          <div className="product-meta-row">
                            <span className="product-prep-time">
                              {product.tiempo_preparacion
                                ? `${product.tiempo_preparacion} min de preparación`
                                : 'Completa el tiempo de preparación'}
                            </span>
                            <strong>{money(product.precio_venta)}</strong>
                          </div>
                          {!product.sede && (
                            <p className="field-error">Pendiente de asignación de sede.</p>
                          )}
                          {productCategory && !productCategory.activo && (
                            <p className="field-error">Categoría inactiva: oculto al cliente.</p>
                          )}
                          <div className="product-actions">
                            <button
                              className="secondary-button"
                              onClick={() => {
                                setNotice('')
                                setEditor(product)
                              }}
                            >
                              Editar
                            </button>
                            {product.activo && (
                              <button
                                className="danger-link"
                                onClick={() => {
                                  setActionError('')
                                  setTarget(product)
                                }}
                              >
                                Desactivar
                              </button>
                            )}
                          </div>
                        </div>
                      </article>
                    )
                  })}
                </div>
              </>
            )}
          </>
        )}
      </main>

      {target && (
        <ConfirmarDesactivacion
          product={target}
          busy={busy}
          error={actionError}
          onConfirm={deactivate}
          onCancel={() => setTarget(null)}
        />
      )}

      {categoryTarget && (
        <div className="category-delete-backdrop" role="presentation">
          <section
            className="category-delete-dialog"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="delete-category-title"
          >
            <span className="login-kicker">ELIMINAR CATEGORÍA</span>
            <h2 id="delete-category-title">{categoryTarget.nombre}</h2>
            <p>
              Esta acción eliminará la categoría. Solo podrás continuar si no tiene productos
              asociados.
            </p>
            {actionError && (
              <p className="error-message" role="alert">
                {actionError}
              </p>
            )}
            <div className="form-actions">
              <button
                className="secondary-button"
                onClick={() => setCategoryTarget(null)}
                disabled={categoryBusy}
              >
                Cancelar
              </button>
              <button className="danger-link" onClick={deleteCategory} disabled={categoryBusy}>
                {categoryBusy ? 'Eliminando…' : 'Eliminar categoría'}
              </button>
            </div>
          </section>
        </div>
      )}
    </section>
  )
}