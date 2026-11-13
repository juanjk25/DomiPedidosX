import { useEffect, useMemo, useState } from 'react'
import { api } from './api.js'
import RegistroCliente from './pages/RegistroCliente.jsx'
import MenuPromociones from './pages/MenuPromociones.jsx'
import PanelOperador from './pages/PanelOperador.jsx' 

function AuthPanel({ register, setRegister, onAuthenticated }) {
  const [form, setForm] = useState({
    email: '', password: '', first_name: '', last_name: '', phone: '',
    phone_extension: '', tipo_documento: 'CC', numero_documento: '',
    date_of_birth: '', delivery_address: '', address_reference: '',
  })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const update = event => {
    const numericFields = ['numero_documento', 'phone', 'phone_extension']
    const value = numericFields.includes(event.target.name)
      ? event.target.value.replace(/\D/g, '')
      : event.target.value
    setForm(current => ({ ...current, [event.target.name]: value }))
  }

async function submit(event) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      let tokens;
      if (register) {
        const accountData = {
          email: form.email,
          password: form.password,
          nombres: form.first_name,
          apellidos: form.last_name,
          tipo_documento: form.tipo_documento,
          numero_documento: form.numero_documento,
          telefono_cliente: form.phone,
          extension_telefonica: form.phone_extension,
          direccion_residencia: form.delivery_address,
          referencia_direccion: form.address_reference,
          fecha_nacimiento: form.date_of_birth,
        }
        const registered = await api('/auth/register/', { method: 'POST', body: JSON.stringify(accountData) })
        tokens = await api('/auth/token/', { method: 'POST', body: JSON.stringify({ username: registered.username, password: form.password }) })
      } else {
        tokens = await api('/auth/token/', { method: 'POST', body: JSON.stringify({ username: form.email, password: form.password }) })
      }
      
      localStorage.setItem('domi_access', tokens.access)
      localStorage.setItem('domi_refresh', tokens.refresh)
      
      // Extrae el rol de la respuesta HTTP (tokens.user.role) o del token (payload.role)
      let detectedRole = tokens.user?.role
      if (!detectedRole && tokens.access) {
        try {
          const payload = JSON.parse(atob(tokens.access.split('.')[1]))
          detectedRole = payload.role || payload.user?.role
        } catch (e) {
          console.error('Error parseando token:', e)
        }
      }

      const finalRole = detectedRole || 'cliente'
      localStorage.setItem('domi_role', finalRole)
      
      onAuthenticated(form.delivery_address, finalRole)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (register) {
    return <RegistroCliente form={form} update={update} error={error} busy={busy} onSubmit={submit} onBackToLogin={() => { setRegister(false); setError('') }} />
  }

  return <section className="login-page">
    <div className="login-brand"><span className="brand-mark">D</span><strong>DomiPedidos<span className="brand-x">X</span></strong></div>
    <div className="login-card">
      <span className="login-kicker">CUENTA DOMIPEDIDOS</span>
      <h1>Qué bueno verte</h1>
      <p>Inicia sesión para descubrir el menú de hoy.</p>
      <form onSubmit={submit} autoComplete="off">
        <label>Correo electrónico<input type="email" name="email" value={form.email} onChange={update} autoComplete="username" required /></label>
        <label>Contraseña<input type="password" name="password" value={form.password} onChange={update} autoComplete="current-password" required /></label>
        {error && <p className="error-message">{error}</p>}
        <button className="primary-button" disabled={busy}>{busy ? 'Ingresando…' : 'Iniciar sesión'} <span>→</span></button>
      </form>
      <button className="link-button" onClick={() => setRegister(true)}>Crear una cuenta de cliente</button>
    </div>
  </section>
}

function App() {
  const [authenticated, setAuthenticated] = useState(() => !!localStorage.getItem('domi_access'))
  const [userRole, setUserRole] = useState(() => localStorage.getItem('domi_role') || 'cliente')
  const [authMode, setAuthMode] = useState('login')
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [cart, setCart] = useState({})
  const [address, setAddress] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    // NUEVO CONDICIONAL: Solo cargar el menú si es cliente
    if (authenticated && userRole === 'cliente') {
      Promise.all([api('/categories/'), api('/products/')])
        .then(([categoryData, productData]) => {
          setCategories(categoryData.map(item => ({ id: item.nombre, name: item.nombre })))
          setProducts(productData.map(item => ({
            id: item.id_producto,
            name: item.nombre_producto,
            price: item.precio_venta,
            category_name: item.tipo_de_producto,
            description: 'Masa artesanal y tus ingredientes favoritos.',
          })))
        })
        .catch(err => setError(err.message))
    }
  }, [authenticated, userRole]) 

  const cartItems = useMemo(() => Object.entries(cart)
    .map(([id, quantity]) => ({ product: products.find(item => String(item.id) === id), quantity }))
    .filter(item => item.product), [cart, products])

  function addProduct(product) {
    setCart(current => ({ ...current, [product.id]: (current[product.id] || 0) + 1 }))
    setNotice(`${product.name} agregado al pedido`)
    setTimeout(() => setNotice(''), 2200)
  }

  function changeQuantity(productId, delta) {
    setCart(current => {
      const next = { ...current }
      const quantity = (next[productId] || 0) + delta
      if (quantity <= 0) delete next[productId]
      else next[productId] = quantity
      return next
    })
  }

function logout() {
    localStorage.removeItem('domi_access')
    localStorage.removeItem('domi_refresh')
    localStorage.removeItem('domi_role')
    setAuthenticated(false)
    setUserRole('cliente')
    setAuthMode('login')
    setCart({})
  }

  async function checkout() {
    if (!cartItems.length) {
      setError('Agrega al menos un producto al pedido.')
      return
    }
    if (!address.trim()) {
      setError('Escribe una dirección de entrega.')
      return
    }
    setError('')
    try {
      const branches = await api('/branches/')
      const branchId = branches[0]?.id_sede
      if (!branchId) throw new Error('No hay una sede disponible para recibir pedidos.')
      await api('/orders/', {
        method: 'POST',
        body: JSON.stringify({
          sede: branchId,
          direccion_entrega: address.trim(),
          items: cartItems.map(item => ({ producto_id: item.product.id, cantidad: item.quantity })),
        }),
      })
      setCart({})
      setNotice('Pedido confirmado correctamente')
      setTimeout(() => setNotice(''), 3000)
    } catch (err) {
      setError(err.message)
    }
  }

  return <div className="app-shell">
    {!authenticated
      ? <AuthPanel 
          key={authMode} 
          register={authMode === 'register'} 
          setRegister={value => setAuthMode(value ? 'register' : 'login')} 
          onAuthenticated={(initialAddress, role) => { 
            setAddress(initialAddress || '')
            setUserRole(role) // NUEVO: Guardar el rol
            setAuthenticated(true) 
          }} 
        />
      : userRole === 'operator' 
        ? <PanelOperador onLogout={logout} onError={setError} /> // NUEVO: Renderizar panel de operador
        : <MenuPromociones 
            products={products} 
            categories={categories} 
            cartItems={cartItems} 
            address={address} 
            error={error} 
            onError={setError} 
            onAddressChange={setAddress} 
            onAdd={addProduct} 
            onChangeQuantity={changeQuantity} 
            onCheckout={checkout} 
            onLogout={logout} 
          />
    }
    {notice && <div className="toast">✓ {notice}</div>}
  </div>
}

export default App
