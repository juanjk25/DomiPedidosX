import React from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import IniciarSesion from '../../src/pages/IniciarSesion.jsx'
import RecuperarContrasena from '../../src/pages/RecuperarContrasena.jsx'
import RestablecerContrasena from '../../src/pages/RestablecerContrasena.jsx'
import ProductoForm from '../../src/components/ProductoForm.jsx'
import GestionMenu from '../../src/pages/GestionMenu.jsx'
import MenuPromociones from '../../src/pages/MenuPromociones.jsx'
import { api, clearSession, saveTokens } from '../../src/api.js'
vi.mock('../../src/api.js', () => ({ api: vi.fn(), clearSession: vi.fn(), saveTokens: vi.fn() }))
const branches = [{ id_sede: 1, nombre_sede: 'Centro' }]
const categories = [{ id: 1, nombre: 'Comida', sede: 1, activo: true }, { id: 2, nombre: 'Retirada', sede: 1, activo: false }]
const product = { id_producto: 5, nombre_producto: 'Pizza', codigo_de_barras: '001', sede: 1, categoria: 1, tipo_de_producto: 'Comida', imagen_url: 'https://example.org/pizza.jpg', tiempo_preparacion: 15, precio_venta: '20000.00', precio_compra: '10000.00', activo: true }
beforeEach(() => { vi.resetAllMocks(); window.history.replaceState({}, '', '/') })

describe('A4 inicio de sesión', () => {
  it('marca los obligatorios vacíos sin enviar la solicitud y enfoca el primero', async () => {
    render(<IniciarSesion onAuthenticated={vi.fn()} navigate={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: 'Iniciar sesión', exact: true }))
    expect(screen.getByLabelText('Correo electrónico o usuario')).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByLabelText('Contraseña')).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByLabelText('Correo electrónico o usuario')).toHaveFocus()
    expect(screen.getByText('Escribe tu contraseña.')).toBeInTheDocument()
    expect(api).not.toHaveBeenCalled()
  })
  it('envía credenciales, guarda tokens y carga el perfil', async () => {
    const u = userEvent.setup(), ready = vi.fn().mockResolvedValue()
    api.mockResolvedValue({ access: 'access', refresh: 'refresh' })
    render(<IniciarSesion onAuthenticated={ready} navigate={vi.fn()} />)
    await u.type(screen.getByLabelText('Correo electrónico o usuario'), 'CLIENTE@example.org')
    await u.type(screen.getByLabelText('Contraseña'), 'ClavePrueba-489!')
    await u.click(screen.getByRole('button', { name: 'Iniciar sesión', exact: true }))
    expect(api.mock.calls[0][0]).toBe('/auth/login/')
    expect(JSON.parse(api.mock.calls[0][1].body).username).toBe('cliente@example.org')
    expect(saveTokens).toHaveBeenCalledWith({ access: 'access', refresh: 'refresh' })
    expect(ready).toHaveBeenCalledOnce()
  })
  it('muestra error 401 sin autenticar', async () => {
    api.mockRejectedValue({ status: 401 })
    const u = userEvent.setup(), ready = vi.fn()
    render(<IniciarSesion onAuthenticated={ready} navigate={vi.fn()} />)
    await u.type(screen.getByLabelText('Correo electrónico o usuario'), 'usuario')
    await u.type(screen.getByLabelText('Contraseña'), 'incorrecta')
    await u.click(screen.getByRole('button', { name: 'Iniciar sesión', exact: true }))
    expect(await screen.findByRole('alert')).toHaveTextContent('incorrectos')
    expect(ready).not.toHaveBeenCalled(); expect(clearSession).toHaveBeenCalled()
  })
  it('permite mostrar contraseña y navegar a recuperación', async () => {
    const u = userEvent.setup(), navigate = vi.fn()
    render(<IniciarSesion onAuthenticated={vi.fn()} navigate={navigate} />)
    await u.click(screen.getByRole('button', { name: 'Mostrar contraseña' }))
    expect(screen.getByLabelText('Contraseña')).toHaveAttribute('type', 'text')
    await u.click(screen.getByRole('button', { name: '¿Olvidaste tu contraseña?' }))
    expect(navigate).toHaveBeenCalledWith('/recuperar-contrasena')
  })
})
describe('A6 recuperación', () => {
  it('bloquea doble envío y muestra confirmación genérica', async () => {
    let finish; api.mockImplementation(() => new Promise(resolve => { finish = resolve }))
    const u = userEvent.setup()
    render(<RecuperarContrasena navigate={vi.fn()} />)
    await u.type(screen.getByLabelText('Correo electrónico registrado'), 'cliente@example.org')
    await u.click(screen.getByRole('button', { name: 'Enviar enlace de recuperación' }))
    expect(screen.getByRole('button', { name: 'Enviando…' })).toBeDisabled()
    finish({ message: 'ok' })
    expect(await screen.findByRole('status')).toHaveTextContent('Si existe una cuenta')
    expect(api).toHaveBeenCalledTimes(1)
    expect(api.mock.calls[0][0]).toBe('/auth/password-reset/')
  })
  it('no anuncia éxito cuando falla la red', async () => {
    api.mockRejectedValue(new Error('Sin conexión'))
    const u = userEvent.setup()
    render(<RecuperarContrasena navigate={vi.fn()} />)
    await u.type(screen.getByLabelText('Correo electrónico registrado'), 'cliente@example.org')
    await u.click(screen.getByRole('button', { name: 'Enviar enlace de recuperación' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Sin conexión')
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
  it('el correo inválido no se envía', async () => {
    const u = userEvent.setup()
    render(<RecuperarContrasena navigate={vi.fn()} />)
    await u.type(screen.getByLabelText('Correo electrónico registrado'), 'no-es-correo')
    await u.click(screen.getByRole('button', { name: 'Enviar enlace de recuperación' }))
    expect(api).not.toHaveBeenCalled()
  })
  it('valida coincidencia y consume uid/token del enlace', async () => {
    window.history.replaceState({}, '', '/restablecer-contrasena?uid=MQ&token=prueba')
    api.mockResolvedValue({ message: 'ok' })
    const u = userEvent.setup(), reset = vi.fn()
    render(<RestablecerContrasena navigate={vi.fn()} onReset={reset} />)
    await u.type(screen.getByLabelText('Nueva contraseña', { exact: true }), 'NuevaClave-123!')
    await u.type(screen.getByLabelText('Confirmar nueva contraseña'), 'OtraClave-123!')
    await u.click(screen.getByRole('button', { name: 'Guardar nueva contraseña' }))
    expect(screen.getByRole('alert')).toHaveTextContent('no coinciden'); expect(api).not.toHaveBeenCalled()
    await u.clear(screen.getByLabelText('Confirmar nueva contraseña'))
    await u.type(screen.getByLabelText('Confirmar nueva contraseña'), 'NuevaClave-123!')
    await u.click(screen.getByRole('button', { name: 'Guardar nueva contraseña' }))
    expect(await screen.findByRole('status')).toHaveTextContent('actualizó correctamente')
    expect(JSON.parse(api.mock.calls[0][1].body)).toEqual({ uid: 'MQ', token: 'prueba', new_password: 'NuevaClave-123!' })
    expect(window.location.search).toBe(''); expect(reset).toHaveBeenCalledOnce()
  })
  it('identifica un enlace incompleto', () => {
    render(<RestablecerContrasena navigate={vi.fn()} />)
    expect(screen.getByRole('alert')).toHaveTextContent('incompleto')
    expect(screen.queryByRole('button', { name: 'Guardar nueva contraseña' })).not.toBeInTheDocument()
  })
})
describe('B5 B6 formulario de producto', () => {
  it('solo permite seleccionar categorías de la sede elegida', async () => {
    const other = { id: 3, nombre: 'Categoría de Norte', sede: 2, activo: true }
    render(<ProductoForm categories={[...categories, other]} branches={[...branches, { id_sede: 2, nombre_sede: 'Norte' }]} branchId="1" onSaved={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.queryByRole('option', { name: 'Categoría de Norte' })).not.toBeInTheDocument()
    await userEvent.selectOptions(screen.getByLabelText(/Categoría/), '1')
    await userEvent.selectOptions(screen.getByLabelText(/Sede/), '2')
    expect(screen.getByRole('option', { name: 'Categoría de Norte' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'Comida' })).not.toBeInTheDocument()
    expect(screen.getByLabelText(/Categoría/)).toHaveValue('')
  })
  it('exige campos obligatorios antes de crear', async () => {
    render(<ProductoForm categories={categories} branches={branches} branchId="1" onSaved={vi.fn()} onCancel={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: 'Crear producto' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Revisa los campos')
    expect(screen.getByLabelText(/Nombre del producto/)).toHaveAttribute('aria-invalid', 'true')
    expect(api).not.toHaveBeenCalled()
  })
  it('crea con todos los atributos mediante POST', async () => {
    api.mockResolvedValue(product)
    const u = userEvent.setup(), saved = vi.fn()
    render(<ProductoForm categories={categories} branches={branches} branchId="1" onSaved={saved} onCancel={vi.fn()} />)
    await u.type(screen.getByLabelText(/Nombre del producto/), 'Pizza nueva')
    await u.type(screen.getByLabelText(/Código de barras/), '002')
    await u.type(screen.getByLabelText(/Precio de venta/), '22000')
    await u.selectOptions(screen.getByLabelText(/Categoría/), '1')
    await u.type(screen.getByLabelText(/Tiempo de preparación/), '18')
    await u.type(screen.getByLabelText(/URL de la imagen/), 'https://example.org/pizza.png')
    await u.click(screen.getByRole('button', { name: 'Crear producto' }))
    expect(api.mock.calls[0][0]).toBe('/management/products/')
    expect(api.mock.calls[0][1].method).toBe('POST')
    expect(JSON.parse(api.mock.calls[0][1].body)).toMatchObject({ nombre_producto: 'Pizza nueva', sede: 1, categoria: 1, tiempo_preparacion: 18, activo: true })
    expect(saved).toHaveBeenCalledWith('Producto creado y asociado a la sede.')
  })
  it('impide guardar cuando no existen categorías activas', () => {
    render(<ProductoForm categories={[]} branches={branches} branchId="1" onSaved={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Crear producto' })).toBeDisabled()
    expect(screen.getByText(/No hay categorías activas/)).toBeInTheDocument()
  })
  it('edita campos y envía PATCH con la sede conservada', async () => {
    api.mockResolvedValue(product)
    const u = userEvent.setup(), saved = vi.fn()
    render(<ProductoForm product={product} categories={categories} branches={branches} branchId="1" onSaved={saved} onCancel={vi.fn()} />)
    await u.clear(screen.getByLabelText(/Nombre del producto/)); await u.type(screen.getByLabelText(/Nombre del producto/), 'Pizza editada')
    await u.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    expect(api.mock.calls[0][0]).toBe('/management/products/5/')
    expect(api.mock.calls[0][1].method).toBe('PATCH')
    expect(JSON.parse(api.mock.calls[0][1].body)).toMatchObject({ nombre_producto: 'Pizza editada', sede: 1, categoria: 1 })
    expect(saved).toHaveBeenCalledWith('Producto actualizado.')
  })
  it('conserva los datos y muestra el error de un código duplicado', async () => {
    api.mockRejectedValue({ message: 'Código ya existe', fields: { codigo_de_barras: ['Código duplicado'] } })
    render(<ProductoForm product={product} categories={categories} branches={branches} branchId="1" onSaved={vi.fn()} onCancel={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Código ya existe')
    expect(screen.getByLabelText(/Nombre del producto/)).toHaveValue('Pizza')
    expect(screen.getByRole('button', { name: 'Guardar cambios' })).toBeEnabled()
  })
})
describe('B4 B8 gestión y vista del cliente', () => {
  it('cancelar no modifica; confirmar cambia el estado sin borrar el producto', async () => {
    let current = { ...product }
    api.mockImplementation(async (path, options = {}) => {
      if (path.includes('categories')) return categories
      if (path.includes('branches')) return branches
      if (options.method === 'PATCH') { current = { ...current, activo: false }; return current }
      return [current]
    })
    const u = userEvent.setup()
    render(<GestionMenu onPreview={vi.fn()} onLogout={vi.fn()} />)
    await screen.findByRole('heading', { name: 'Pizza', exact: true })
    await u.click(screen.getByRole('button', { name: 'Desactivar', exact: true }))
    await u.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Cancelar', exact: true }))
    expect(api.mock.calls.filter(([, options]) => options?.method === 'PATCH')).toHaveLength(0)
    await u.click(screen.getByRole('button', { name: 'Desactivar', exact: true }))
    await u.click(screen.getByRole('button', { name: 'Confirmar desactivación' }))
    await waitFor(() => expect(screen.getByText('Inactivo', { exact: true })).toBeInTheDocument())
    expect(screen.getByRole('heading', { name: 'Pizza', exact: true })).toBeInTheDocument()
    expect(api.mock.calls.find(([, options]) => options?.method === 'PATCH')[1].body).toBe('{"activo":false}')
  })
  it('un error de desactivación no anuncia éxito y mantiene abierto el diálogo', async () => {
    api.mockImplementation(async (path, options = {}) => {
      if (options.method === 'PATCH') throw new Error('No se pudo desactivar')
      if (path.includes('categories')) return categories
      if (path.includes('branches')) return branches
      return [product]
    })
    render(<GestionMenu onPreview={vi.fn()} onLogout={vi.fn()} />)
    await screen.findByRole('heading', { name: 'Pizza', exact: true })
    await userEvent.click(screen.getByRole('button', { name: 'Desactivar', exact: true }))
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar desactivación' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo desactivar')
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Activo', { exact: true })).toBeInTheDocument()
  })
  it('el menú reacciona a productos actualizados y a su retirada', () => {
    const props = { categories: [{ id: 1, name: 'Comida' }], cartItems: [], address: '', onAdd: vi.fn(), onChangeQuantity: vi.fn(), onCheckout: vi.fn(), onLogout: vi.fn(), onAddressChange: vi.fn(), onError: vi.fn() }
    const { rerender } = render(<MenuPromociones {...props} products={[{ id: 1, name: 'Pizza', price: '20000', category_name: 'Comida' }]} />)
    expect(screen.getByRole('heading', { name: 'Pizza', exact: true })).toBeInTheDocument()
    rerender(<MenuPromociones {...props} products={[{ id: 1, name: 'Pizza nueva', price: '23000', category_name: 'Comida' }]} />)
    expect(screen.getByRole('heading', { name: 'Pizza nueva' })).toBeInTheDocument()
    rerender(<MenuPromociones {...props} products={[]} />)
    expect(screen.queryByRole('heading', { name: 'Pizza nueva' })).not.toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('No hay productos disponibles')
  })
})
