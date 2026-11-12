// Los permisos efectivos siempre los comprueba la API.
export function homeFor(user) {
  if (user.can_manage_menu) return '/gestion-menu'
  if (user.role === 'customer') return '/menu'
  return '/personal'
}
export function roleLabel(role) {
  return { admin: 'Administración', operator: 'Operación de sede', customer: 'Cliente', kitchen: 'Cocina', courier: 'Reparto' }[role] || 'Cuenta sin asignación'
}
