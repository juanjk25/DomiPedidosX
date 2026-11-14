import React from 'react'
import { beforeEach, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../../src/App.jsx'
import { api } from '../../src/api.js'
vi.mock('../../src/api.js', () => ({ api: vi.fn(), clearSession: vi.fn(), getToken: () => null }))
vi.mock('../../src/pages/IniciarSesion.jsx', () => ({ default: ({ onAuthenticated }) => <button onClick={onAuthenticated}>Entrar</button> }))
vi.mock('../../src/pages/GestionMenu.jsx', () => ({ default: () => <h1>Gestionar menú</h1> }))
vi.mock('../../src/pages/MenuPromociones.jsx', () => ({ default: () => <h1>Menú del cliente</h1> }))
beforeEach(() => { window.history.replaceState({}, '', '/login'); window.scrollTo = vi.fn(); vi.resetAllMocks() })
it.each([
  ['customer', false, '/menu', 'Menú del cliente'],
  ['operator', true, '/gestion-menu', 'Gestionar menú'],
  ['admin', true, '/gestion-menu', 'Gestionar menú'],
  ['kitchen', false, '/personal', 'Cocina'],
  ['courier', false, '/personal', 'Reparto'],
  [null, false, '/personal', 'Cuenta sin asignación'],
])('A4: dirige %s a su sección y no expone el carrito a personal', async (role, can_manage_menu, path, heading) => {
  api.mockImplementation(async endpoint => endpoint === '/me/' ? { role, can_manage_menu, username: 'prueba', sede: 1 } : [])
  render(<App />)
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
  expect(await screen.findByRole('heading', { name: heading })).toBeInTheDocument()
  await waitFor(() => expect(window.location.pathname).toBe(path))
  if (role === 'kitchen' || role === 'courier') expect(screen.queryByRole('heading', { name: 'Menú del cliente' })).not.toBeInTheDocument()
})
