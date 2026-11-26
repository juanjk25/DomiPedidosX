import { useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'

export default function GestionPersonal({ user, onBack, onLogout }) {
  const [members, setMembers] = useState([])
  const [audits, setAudits] = useState([])
  const [tab, setTab] = useState('personal')
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [pendingAction, setPendingAction] = useState(null)
  const [motivo, setMotivo] = useState('')

  async function loadData() {
    setLoading(true)
    setError('')
    try {
      const [teamData, auditData] = await Promise.all([
        api('/team-members/'),
        api('/team-members/audit/'),
      ])
      setMembers(Array.isArray(teamData) ? teamData : [])
      setAudits(Array.isArray(auditData) ? auditData : [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return members.filter(m => {
      const matchesStatus =
        statusFilter === 'all' ||
        (statusFilter === 'active' && m.is_active) ||
        (statusFilter === 'inactive' && !m.is_active)
      const haystack = `${m.username || ''} ${m.email || ''} ${m.first_name || ''} ${m.last_name || ''} ${m.rol || ''}`.toLowerCase()
      return matchesStatus && (!q || haystack.includes(q))
    })
  }, [members, query, statusFilter])

  async function confirmStatusChange(event) {
    event.preventDefault()
    if (!pendingAction || busyId) return
    const { member, nextActive } = pendingAction
    setBusyId(member.id)
    setError('')
    setNotice('')
    try {
      await api(`/team-members/${member.id}/status/`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: nextActive, motivo: motivo.trim() }),
      })
      setPendingAction(null)
      setMotivo('')
      setNotice(
        nextActive
          ? `Cuenta de ${member.username} reactivada correctamente.`
          : `Cuenta de ${member.username} desactivada correctamente.`
      )
      await loadData()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  const isSelf = member =>
    member.id === user?.id || (member.username && member.username === user?.username)

  return (
    <section className="management-page">
      <header className="management-header">
        <div className="menu-sidebar-brand">
          <span className="brand-mark">D</span>DomiPedidos<span className="brand-x">X</span>
        </div>
        <nav aria-label="Menú de administrador">
          {onBack && <button onClick={onBack}>Volver</button>}
          <button onClick={onLogout}>Cerrar sesión</button>
        </nav>
      </header>

      <main className="management-main">
        <div className="management-title">
          <div>
            <span className="login-kicker">ADMINISTRACIÓN</span>
            <h1>Gestión de personal</h1>
            <p>Activa o desactiva cuentas del equipo y consulta el historial de auditoría.</p>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              className={tab === 'personal' ? 'primary-button' : 'secondary-button'}
              onClick={() => setTab('personal')}
            >
              Personal ({members.length})
            </button>
            <button
              className={tab === 'auditoria' ? 'primary-button' : 'secondary-button'}
              onClick={() => setTab('auditoria')}
            >
              Auditoría ({audits.length})
            </button>
          </div>
        </div>

        {notice && <p className="status-message" role="status">{notice}</p>}
        {error && (
          <p className="error-message" role="alert">
            {error}{' '}
            <button className="inline-link" onClick={loadData}>Reintentar</button>
          </p>
        )}

        {pendingAction && (
          <form
            onSubmit={confirmStatusChange}
            style={{
              border: '1px solid #ddd',
              borderRadius: '8px',
              padding: '1rem',
              marginBottom: '1.5rem',
              background: '#fff',
            }}
          >
            <p style={{ marginBottom: '0.75rem' }}>
              <strong>
                {pendingAction.nextActive ? 'Reactivar' : 'Desactivar'} cuenta:
              </strong>{' '}
              {pendingAction.member.username} ({pendingAction.member.email})
            </p>
            <label style={{ display: 'block', marginBottom: '0.75rem' }}>
              Motivo (opcional)
              <input
                type="text"
                maxLength={255}
                value={motivo}
                onChange={e => setMotivo(e.target.value)}
                placeholder="Ej. Vacaciones, cambio de turno, reingreso..."
                style={{ width: '100%', marginTop: '0.25rem' }}
              />
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                type="submit"
                className="primary-button"
                disabled={busyId === pendingAction.member.id}
              >
                {busyId === pendingAction.member.id ? 'Guardando…' : 'Confirmar cambio'}
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={() => { setPendingAction(null); setMotivo('') }}
              >
                Cancelar
              </button>
            </div>
          </form>
        )}

        {loading ? (
          <p role="status">Cargando información de personal…</p>
        ) : tab === 'personal' ? (
          <>
            <div className="management-stats">
              <div><strong>{members.length}</strong><span>Total personal</span></div>
              <div><strong>{members.filter(m => m.is_active).length}</strong><span>Activos</span></div>
              <div><strong>{members.filter(m => !m.is_active).length}</strong><span>Inactivos</span></div>
            </div>

            <div className="management-filters">
              <label>
                Buscar integrante
                <input
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Usuario, correo o rol"
                />
              </label>
              <label>
                Estado
                <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                  <option value="all">Todos</option>
                  <option value="active">Activos</option>
                  <option value="inactive">Inactivos</option>
                </select>
              </label>
            </div>

            {!filtered.length ? (
              <div className="empty-state">
                <h2>No hay integrantes para mostrar</h2>
                <p>Ajusta los filtros de búsqueda.</p>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #ddd' }}>
                      <th style={{ padding: '0.75rem' }}>Usuario</th>
                      <th style={{ padding: '0.75rem' }}>Correo</th>
                      <th style={{ padding: '0.75rem' }}>Rol</th>
                      <th style={{ padding: '0.75rem' }}>Estado</th>
                      <th style={{ padding: '0.75rem', textAlign: 'right' }}>Acción</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map(member => (
                      <tr key={member.id} style={{ borderBottom: '1px solid #eee' }}>
                        <td style={{ padding: '0.75rem' }}>
                          <strong>{member.username}</strong>
                          {isSelf(member) && <small> (Tu sesión)</small>}
                        </td>
                        <td style={{ padding: '0.75rem' }}>{member.email || '—'}</td>
                        <td style={{ padding: '0.75rem' }}>{member.rol || 'Personal'}</td>
                        <td style={{ padding: '0.75rem' }}>
                          <span className={`status-pill ${member.is_active ? 'active' : 'inactive'}`}>
                            {member.is_active ? 'Activo' : 'Inactivo'}
                          </span>
                        </td>
                        <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                          {isSelf(member) ? (
                            <small>No editable</small>
                          ) : member.is_active ? (
                            <button
                              className="danger-link"
                              disabled={busyId === member.id}
                              onClick={() => {
                                setError('')
                                setPendingAction({ member, nextActive: false })
                              }}
                            >
                              Desactivar
                            </button>
                          ) : (
                            <button
                              className="secondary-button"
                              disabled={busyId === member.id}
                              onClick={() => {
                                setError('')
                                setPendingAction({ member, nextActive: true })
                              }}
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
          </>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            {!audits.length ? (
              <div className="empty-state">
                <h2>Sin registros de auditoría</h2>
                <p>Los cambios de estado del personal aparecerán aquí.</p>
              </div>
            ) : (
              <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #ddd' }}>
                    <th style={{ padding: '0.75rem' }}>Fecha</th>
                    <th style={{ padding: '0.75rem' }}>Administrador</th>
                    <th style={{ padding: '0.75rem' }}>Usuario afectado</th>
                    <th style={{ padding: '0.75rem' }}>Cambio</th>
                    <th style={{ padding: '0.75rem' }}>Motivo</th>
                  </tr>
                </thead>
                <tbody>
                  {audits.map(item => (
                    <tr key={item.id} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '0.75rem' }}>
                        {new Date(item.fecha_hora).toLocaleString('es-CO')}
                      </td>
                      <td style={{ padding: '0.75rem' }}>{item.administrador_username}</td>
                      <td style={{ padding: '0.75rem' }}>{item.usuario_afectado_username}</td>
                      <td style={{ padding: '0.75rem' }}>
                        {item.estado_anterior ? 'Activo' : 'Inactivo'} →{' '}
                        <strong>{item.estado_nuevo ? 'Activo' : 'Inactivo'}</strong>
                      </td>
                      <td style={{ padding: '0.75rem' }}>{item.motivo || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </main>
    </section>
  )
}