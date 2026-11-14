import AuthLayout from '../components/AuthLayout.jsx'
import { roleLabel } from '../utils/session.js'

// Punto de entrada de A4. Los módulos operativos los integra su responsable.
export default function InicioPersonal({ user, onLogout }) {
  return <AuthLayout title={roleLabel(user.role)} description={`Sesión de ${user.username || user.email}`}>
    <p className="status-message" role="status">Has iniciado sesión correctamente.{user.sede ? ` Sede asignada: ${user.sede}.` : ''}</p>
    <p>{user.role ? 'Tu cuenta de personal está activa. Aún no hay tareas disponibles en esta sección.' : 'Solicita al administrador que complete tu asignación de rol y sede.'}</p>
    <button className="primary-button full" onClick={onLogout}>Cerrar sesión</button>
  </AuthLayout>
}
