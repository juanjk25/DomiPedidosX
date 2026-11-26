import { useEffect, useState } from 'react'
import { api } from '../api.js'

export default function PanelOperador({
  onOpenMenu,
  onOpenInventory,
  onOpenTeam,
  onLogout,
  onError,
}) {
  const [activeTab, setActiveTab] = useState('categorias')
  const [categorias, setCategorias] = useState([])
  const [nuevaCategoria, setNuevaCategoria] = useState('')
  const [busy, setBusy] = useState(false)
  const [mensaje, setMensaje] = useState('')
  const [localError, setLocalError] = useState('')

  const reportError = msg => {
    setLocalError(msg)
    if (onError) onError(msg)
  }

  useEffect(() => {
    cargarCategorias()
  }, [])

  async function cargarCategorias() {
    setLocalError('')
    try {
      const data = await api('/management/categories/')
      setCategorias(Array.isArray(data) ? data : [])
    } catch (err) {
      reportError('Error al cargar categorías: ' + err.message)
    }
  }

  async function crearCategoria(e) {
    e.preventDefault()
    if (!nuevaCategoria.trim()) return
    setBusy(true)
    setLocalError('')
    try {
      await api('/management/categories/', {
        method: 'POST',
        body: JSON.stringify({ nombre: nuevaCategoria.trim(), activo: true }),
      })
      setNuevaCategoria('')
      setMensaje('Categoría creada exitosamente')
      setTimeout(() => setMensaje(''), 3000)
      cargarCategorias()
    } catch (err) {
      reportError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function alternarEstado(id, estadoActual, nombre) {
    if (!estadoActual && !window.confirm(`¿Estás seguro de habilitar la categoría ${nombre}?`)) return
    if (
      estadoActual &&
      !window.confirm(
        `¿Estás seguro de deshabilitar la categoría ${nombre}? Los productos asociados dejarán de mostrarse.`
      )
    )
      return

    setLocalError('')
    try {
      await api(`/management/categories/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ activo: !estadoActual }),
      })
      cargarCategorias()
    } catch (err) {
      reportError(err.message)
    }
  }

  return (
    <div className="admin-layout" style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '2rem',
          gap: '1rem',
          flexWrap: 'wrap',
        }}
      >
        <div className="login-brand">
          <span className="brand-mark">D</span>
          <strong>Panel Operador</strong>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {onOpenMenu && (
            <button className="secondary-button" onClick={onOpenMenu}>
              Gestionar menú
            </button>
          )}
          {onOpenInventory && (
            <button className="secondary-button" onClick={onOpenInventory}>
              Inventario
            </button>
          )}
          {onOpenTeam && (
            <button className="secondary-button" onClick={onOpenTeam}>
              Gestionar personal
            </button>
          )}
          <button className="link-button" onClick={onLogout}>
            Cerrar sesión
          </button>
        </div>
      </header>

      <nav style={{ borderBottom: '1px solid #ccc', marginBottom: '2rem' }}>
        <button
          style={{
            padding: '0.5rem 1rem',
            borderBottom: activeTab === 'categorias' ? '2px solid black' : 'none',
            background: 'none',
            fontWeight: 'bold',
          }}
          onClick={() => setActiveTab('categorias')}
        >
          Gestión de Categorías
        </button>
      </nav>

      {localError && (
        <p className="error-message" role="alert" style={{ marginBottom: '1rem' }}>
          {localError}
        </p>
      )}

      {activeTab === 'categorias' && (
        <section>
          <h2>Categorías del Menú</h2>

          <form
            onSubmit={crearCategoria}
            style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', marginTop: '1rem' }}
          >
            <input
              type="text"
              placeholder="Nombre de la nueva categoría"
              value={nuevaCategoria}
              onChange={e => setNuevaCategoria(e.target.value)}
              required
              style={{ flex: 1, padding: '0.5rem' }}
            />
            <button className="primary-button" type="submit" disabled={busy}>
              {busy ? 'Creando...' : 'Crear Categoría'}
            </button>
          </form>

          {mensaje && <p style={{ color: 'green', marginBottom: '1rem' }}>{mensaje}</p>}

          <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #eee' }}>
                <th style={{ padding: '0.75rem' }}>ID</th>
                <th style={{ padding: '0.75rem' }}>Nombre</th>
                <th style={{ padding: '0.75rem' }}>Estado</th>
                <th style={{ padding: '0.75rem', textAlign: 'right' }}>Acción</th>
              </tr>
            </thead>
            <tbody>
              {categorias.length === 0 ? (
                <tr>
                  <td colSpan="4" style={{ padding: '1rem', textAlign: 'center' }}>
                    No hay categorías registradas.
                  </td>
                </tr>
              ) : (
                categorias.map(cat => (
                  <tr
                    key={cat.id}
                    style={{ borderBottom: '1px solid #eee', opacity: cat.activo ? 1 : 0.6 }}
                  >
                    <td style={{ padding: '0.75rem' }}>{cat.id}</td>
                    <td style={{ padding: '0.75rem' }}>{cat.nombre}</td>
                    <td style={{ padding: '0.75rem' }}>
                      <span style={{ color: cat.activo ? 'green' : 'red', fontWeight: 'bold' }}>
                        {cat.activo ? 'Habilitada' : 'Deshabilitada'}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                      <button
                        onClick={() => alternarEstado(cat.id, cat.activo, cat.nombre)}
                        style={{
                          padding: '0.5rem 1rem',
                          cursor: 'pointer',
                          background: cat.activo ? '#ffebee' : '#e8f5e9',
                          border: 'none',
                          borderRadius: '4px',
                          color: cat.activo ? '#c62828' : '#2e7d32',
                        }}
                      >
                        {cat.activo ? 'Deshabilitar' : 'Habilitar'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </section>
      )}
    </div>
  )
}