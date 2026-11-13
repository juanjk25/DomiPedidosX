import { useEffect, useState } from 'react'
import { api } from '../api.js'

export default function PanelOperador({ onLogout, onError }) {
  const [activeTab, setActiveTab] = useState('categorias')
  const [categorias, setCategorias] = useState([])
  const [nuevaCategoria, setNuevaCategoria] = useState('')
  const [busy, setBusy] = useState(false)
  const [mensaje, setMensaje] = useState('')

  useEffect(() => {
    cargarCategorias()
  }, [])

  async function cargarCategorias() {
    try {
      const data = await api('/operator/categories/')
      setCategorias(data)
    } catch (err) {
      onError('Error al cargar categorías: ' + err.message)
    }
  }

  async function crearCategoria(e) {
    e.preventDefault()
    if (!nuevaCategoria.trim()) return
    setBusy(true)
    try {
      await api('/operator/categories/', {
        method: 'POST',
        body: JSON.stringify({ nombre: nuevaCategoria.trim(), activa: true })
      })
      setNuevaCategoria('')
      setMensaje('Categoría creada exitosamente')
      setTimeout(() => setMensaje(''), 3000)
      cargarCategorias()
    } catch (err) {
      onError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function alternarEstado(id, estadoActual, nombre) {
    if (!estadoActual && !window.confirm(`¿Estás seguro de habilitar la categoría ${nombre}?`)) return;
    if (estadoActual && !window.confirm(`¿Estás seguro de deshabilitar la categoría ${nombre}? Los productos asociados dejarán de mostrarse.`)) return;

    try {
      await api(`/operator/categories/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ activa: !estadoActual })
      })
      cargarCategorias()
    } catch (err) {
      onError(err.message)
    }
  }

  return (
    <div className="admin-layout" style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div className="login-brand"><span className="brand-mark">D</span><strong>Panel Operador</strong></div>
        <button className="link-button" onClick={onLogout}>Cerrar sesión</button>
      </header>

      <nav style={{ borderBottom: '1px solid #ccc', marginBottom: '2rem' }}>
        <button 
          style={{ padding: '0.5rem 1rem', borderBottom: activeTab === 'categorias' ? '2px solid black' : 'none', background: 'none', fontWeight: 'bold' }}
          onClick={() => setActiveTab('categorias')}
        >
          Gestión de Categorías
        </button>
        {/* Aquí puedes añadir más pestañas en el futuro (ej. Productos, Pedidos) */}
      </nav>

      {activeTab === 'categorias' && (
        <section>
          <h2>Categorías del Menú</h2>
          
          <form onSubmit={crearCategoria} style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', marginTop: '1rem' }}>
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
                <tr><td colSpan="4" style={{ padding: '1rem', textAlign: 'center' }}>No hay categorías registradas.</td></tr>
              ) : categorias.map(cat => (
                <tr key={cat.id_categoria} style={{ borderBottom: '1px solid #eee', opacity: cat.activa ? 1 : 0.6 }}>
                  <td style={{ padding: '0.75rem' }}>{cat.id_categoria}</td>
                  <td style={{ padding: '0.75rem' }}>{cat.nombre}</td>
                  <td style={{ padding: '0.75rem' }}>
                    <span style={{ color: cat.activa ? 'green' : 'red', fontWeight: 'bold' }}>
                      {cat.activa ? 'Habilitada' : 'Deshabilitada'}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                    <button 
                      onClick={() => alternarEstado(cat.id_categoria, cat.activa, cat.nombre)}
                      style={{ padding: '0.5rem 1rem', cursor: 'pointer', background: cat.activa ? '#ffebee' : '#e8f5e9', border: 'none', borderRadius: '4px', color: cat.activa ? '#c62828' : '#2e7d32' }}
                    >
                      {cat.activa ? 'Deshabilitar' : 'Habilitar'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  )
}