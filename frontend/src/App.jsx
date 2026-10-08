import { useEffect, useMemo, useState } from 'react'
import { api, getToken } from './api.js'

const money = value => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(Number(value || 0))

function AuthPanel({ onAuthenticated }) {
  const [register, setRegister] = useState(false)
  const [form, setForm] = useState({ username: '', password: '', first_name: '', last_name: '', email: '', phone: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const update = event => setForm({ ...form, [event.target.name]: event.target.value })
  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true)
    try {
      if (register) await api('/auth/register/', { method: 'POST', body: JSON.stringify(form) })
      const tokens = await api('/auth/token/', { method: 'POST', body: JSON.stringify({ username: form.username, password: form.password }) })
      localStorage.setItem('domi_access', tokens.access); localStorage.setItem('domi_refresh', tokens.refresh); onAuthenticated()
    } catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }
  return <section className="auth-card">
    <div className="eyebrow">CUENTA DOMIPEDIDOS</div><h2>{register ? 'Crea tu cuenta' : 'Qué bueno verte'}</h2>
    <p className="muted">{register ? 'Regístrate para pedir a tu sede favorita.' : 'Inicia sesión para consultar el menú y tus pedidos.'}</p>
    <form onSubmit={submit} className="form-stack">
      {register && <div className="two-fields"><label>Nombre<input name="first_name" value={form.first_name} onChange={update} required /></label><label>Apellido<input name="last_name" value={form.last_name} onChange={update} required /></label></div>}
      {register && <label>Correo<input type="email" name="email" value={form.email} onChange={update} required /></label>}
      <label>Usuario<input name="username" autoComplete="username" value={form.username} onChange={update} required /></label>
      <label>Contraseña<input type="password" name="password" autoComplete={register ? 'new-password' : 'current-password'} minLength="8" value={form.password} onChange={update} required /></label>
      {register && <label>Celular <span className="optional">(opcional)</span><input name="phone" value={form.phone} onChange={update} /></label>}
      {error && <p className="error-message">{error}</p>}
      <button className="button button-dark full" disabled={busy}>{busy ? 'Un momento…' : register ? 'Crear cuenta' : 'Iniciar sesión'}</button>
    </form>
    <button className="text-button" onClick={() => { setRegister(!register); setError('') }}>{register ? 'Ya tengo cuenta' : 'Crear una cuenta de cliente'}</button>
  </section>
}

function App() {
  const [authenticated, setAuthenticated] = useState(Boolean(getToken()))
  const [user, setUser] = useState(null)
  const [profileOpen, setProfileOpen] = useState(false)
  const [profileForm, setProfileForm] = useState({ first_name: '', last_name: '', email: '', phone: '' })
  const [branches, setBranches] = useState([])
  const [branchId, setBranchId] = useState('')
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [categoryId, setCategoryId] = useState('all')
  const [cart, setCart] = useState({})
  const [orders, setOrders] = useState([])
  const [customers, setCustomers] = useState([])
  const [customerId, setCustomerId] = useState('')
  const [addresses, setAddresses] = useState([])
  const [addressId, setAddressId] = useState('new')
  const [addressLabel, setAddressLabel] = useState('Casa')
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [address, setAddress] = useState('')
  const [payment, setPayment] = useState('cash')
  const [notes, setNotes] = useState('')
  const [busy, setBusy] = useState(false)

  async function loadCatalog() {
    try {
      const [branchData, categoryData] = await Promise.all([api('/branches/'), api('/categories/')])
      setBranches(branchData); setCategories(categoryData)
      setBranchId(current => current || String(branchData[0]?.id || ''))
    } catch (err) { setError(err.message) }
  }
  async function loadProducts() {
    if (!branchId) return
    try { setProducts(await api(`/products/?branch=${branchId}${categoryId !== 'all' ? `&category=${categoryId}` : ''}`)) }
    catch (err) { setError(err.message) }
  }
  async function loadAccount() {
    if (!getToken()) return
    try {
      const account = await api('/me/')
      setUser(account)
      setProfileForm({ first_name: account.first_name || '', last_name: account.last_name || '', email: account.email || '', phone: account.profile?.phone || '' })
      if (['operator', 'kitchen', 'courier'].includes(account.profile?.role) && account.profile?.branch) setBranchId(String(account.profile.branch))
      if (account.profile?.role === 'customer') await loadAddresses()
      else { setAddresses([]); setAddress(''); setAddressId('new') }
      if (['operator', 'admin'].includes(account.profile?.role)) {
        try {
          const customerData = await api('/customers/')
          setCustomers(customerData)
          setCustomerId(current => current || String(customerData[0]?.id || ''))
        } catch (err) { setError(err.message) }
      }
    }
    catch { localStorage.removeItem('domi_access'); localStorage.removeItem('domi_refresh'); setAuthenticated(false) }
  }
  async function loadOrders() {
    try { setOrders(await api('/orders/')) } catch (err) { setError(err.message) }
  }
  async function loadAddresses() {
    try {
      const data = await api('/addresses/')
      setAddresses(data)
      const preferred = data.find(item => item.is_default) || data[0]
      if (preferred) { setAddressId(String(preferred.id)); setAddress(preferred.address) }
    } catch (err) { setError(err.message) }
  }
  useEffect(() => { loadCatalog() }, [])
  useEffect(() => { loadProducts() }, [branchId, categoryId])
  useEffect(() => { if (authenticated) { loadAccount(); loadOrders() } }, [authenticated])

  const selectedBranch = branches.find(branch => String(branch.id) === String(branchId))
  const cartItems = useMemo(() => Object.entries(cart).map(([id, quantity]) => ({ product: products.find(p => String(p.id) === id), quantity })).filter(item => item.product), [cart, products])
  const subtotal = cartItems.reduce((sum, item) => sum + Number(item.product.price) * item.quantity, 0)
  const total = subtotal + Number(selectedBranch?.delivery_fee || 0)
  const staffRole = user?.profile?.role
  function add(product) {
    setCart(current => ({ ...current, [String(product.id)]: (current[String(product.id)] || 0) + 1 }))
    setNotice(`${product.name} se agregó al carrito`); setTimeout(() => setNotice(''), 2200)
  }
  function changeQuantity(id, delta) {
    setCart(current => { const next = { ...current }; const amount = (next[id] || 0) + delta; if (amount <= 0) delete next[id]; else next[id] = amount; return next })
  }
  function logout() {
    localStorage.removeItem('domi_access'); localStorage.removeItem('domi_refresh'); setAuthenticated(false); setUser(null); setCart({})
  }
  async function placeOrder(event) {
    event.preventDefault(); setError(''); setBusy(true)
    try {
      const orderPayload = { branch: Number(branchId), delivery_address: address, payment_method: payment, notes, items: cartItems.map(({ product, quantity }) => ({ product_id: product.id, quantity })) }
      if (['operator', 'admin'].includes(staffRole)) orderPayload.customer = Number(customerId)
      const created = await api('/orders/', { method: 'POST', body: JSON.stringify(orderPayload) })
      setCart({}); setNotes(''); setNotice(`Pedido #${created.id} confirmado`)
      await Promise.all([loadOrders(), loadProducts()]); setTimeout(() => setNotice(''), 3500)
    } catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }
  async function updateOrderStatus(orderId, nextStatus) {
    setError('')
    try {
      await api(`/orders/${orderId}/status/`, { method: 'PATCH', body: JSON.stringify({ status: nextStatus }) })
      await loadOrders()
      setNotice(`Pedido #${orderId}: estado actualizado`)
      setTimeout(() => setNotice(''), 2500)
    } catch (err) { setError(err.message) }
  }
  async function cancelOrder(orderId) {
    setError('')
    try {
      await api(`/orders/${orderId}/cancel/`, { method: 'POST', body: JSON.stringify({}) })
      await Promise.all([loadOrders(), loadProducts()])
      setNotice(`Pedido #${orderId} cancelado`); setTimeout(() => setNotice(''), 2500)
    } catch (err) { setError(err.message) }
  }
  async function saveAddress() {
    if (!address.trim()) { setError('Escribe una dirección antes de guardarla.'); return }
    setError('')
    try {
      const saved = await api('/addresses/', { method: 'POST', body: JSON.stringify({ label: addressLabel || 'Casa', address: address.trim(), reference: '', is_default: addresses.length === 0 }) })
      setAddresses(current => [saved, ...current]); setAddressId(String(saved.id)); setAddress(saved.address)
      setNotice('Dirección guardada'); setTimeout(() => setNotice(''), 2500)
    } catch (err) { setError(err.message) }
  }
  async function saveProfile(event) {
    event.preventDefault(); setError('')
    try {
      await api('/me/', { method: 'PATCH', body: JSON.stringify(profileForm) })
      await loadAccount(); setProfileOpen(false); setNotice('Perfil actualizado'); setTimeout(() => setNotice(''), 2500)
    } catch (err) { setError(err.message) }
  }
  const staffActions = {
    received: [['preparing', 'Iniciar preparación'], ['cancelled', 'Cancelar']],
    preparing: [['ready', 'Marcar listo'], ['cancelled', 'Cancelar']],
    ready: [['on_the_way', 'Enviar en camino'], ['delivered', 'Marcar entregado']],
    on_the_way: [['delivered', 'Confirmar entrega']],
  }
  const staffAllowed = {
    operator: ['preparing', 'ready', 'on_the_way', 'delivered', 'cancelled'],
    kitchen: ['preparing', 'ready', 'cancelled'],
    courier: ['on_the_way', 'delivered'],
    admin: ['preparing', 'ready', 'on_the_way', 'delivered', 'cancelled'],
  }

  return <div className="app-shell min-h-screen antialiased">
    <header className="topbar"><a className="brand" href="#"><span className="brand-mark">D</span><span>DomiPedidos<span className="brand-x">X</span></span></a><div className="top-actions">{authenticated ? <><span className="welcome">Hola, {user?.first_name || user?.username || 'cliente'}</span><button className="button button-light" onClick={() => setProfileOpen(value => !value)}>Mi perfil</button><button className="button button-light" onClick={logout}>Salir</button></> : <span className="top-note">Tu antojo, a un pedido de distancia</span>}</div></header>
    <main>
      <section className="hero"><div className="hero-copy"><div className="eyebrow eyebrow-light">HECHO CERCA. LLEGA A TU PUERTA.</div><h1>Lo rico del día,<br /><em>sin complicarte.</em></h1><p>Explora el menú de tu sede y sigue cada paso de tu pedido.</p><div className="hero-meta"><span>✦ Preparado al momento</span><span>⌖ Cali, Colombia</span></div></div><div className="hero-visual"><div className="sun"></div><div className="food-plate"><div className="burger bun-top"></div><div className="burger lettuce"></div><div className="burger patty"></div><div className="burger cheese"></div><div className="burger bun-bottom"></div></div><div className="hero-sticker">RECIÉN<br />HECHO</div></div></section>
      {!authenticated ? <div className="auth-wrap"><AuthPanel onAuthenticated={() => setAuthenticated(true)} /></div> : <>
        {profileOpen && <section className="profile-panel"><form onSubmit={saveProfile} className="profile-form"><div><div className="eyebrow">DATOS DE TU CUENTA</div><h2>Mi perfil</h2></div><div className="profile-fields"><label>Nombre<input value={profileForm.first_name} onChange={event => setProfileForm({ ...profileForm, first_name: event.target.value })} /></label><label>Apellido<input value={profileForm.last_name} onChange={event => setProfileForm({ ...profileForm, last_name: event.target.value })} /></label><label>Correo<input type="email" value={profileForm.email} onChange={event => setProfileForm({ ...profileForm, email: event.target.value })} /></label><label>Celular<input value={profileForm.phone} onChange={event => setProfileForm({ ...profileForm, phone: event.target.value })} /></label></div><button className="button button-dark">Guardar cambios</button></form></section>}
        <div className="section-heading"><div><div className="eyebrow">PIDE EN LÍNEA</div><h2>¿Qué se te antoja?</h2></div><label className="branch-picker">Tu sede<select value={branchId} disabled={["operator", "kitchen", "courier"].includes(staffRole)} onChange={event => { setBranchId(event.target.value); setCart({}) }}>{branches.map(branch => <option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></label></div>
        <div className="content-grid"><section className="menu-area">
          <div className="category-row"><button className={`category-chip ${categoryId === 'all' ? 'active' : ''}`} onClick={() => setCategoryId('all')}>Todo el menú</button>{categories.map(category => <button key={category.id} className={`category-chip ${categoryId === String(category.id) ? 'active' : ''}`} onClick={() => setCategoryId(String(category.id))}>{category.name}</button>)}</div>
          {error && <div className="alert-error">{error}<button onClick={() => setError('')} aria-label="Cerrar">×</button></div>}
          {products.length ? <div className="product-grid">{products.map((product, index) => <article className="product-card" key={product.id}><div className={`product-art art-${index % 4}`}><span>{product.category_name}</span><div className="food-icon">{product.category_name.toLowerCase().includes('bebida') ? '🥤' : '🍔'}</div></div><div className="product-info"><div className="product-title-row"><h3>{product.name}</h3><span className="prep">{product.preparation_minutes} min</span></div><p>{product.description || 'Preparado al momento con ingredientes frescos.'}</p><div className="product-bottom"><strong>{money(product.price)}</strong><button className="add-button" onClick={() => add(product)} aria-label={`Agregar ${product.name}`}>+</button></div></div></article>)}</div> : <div className="empty-state"><div className="empty-icon">✦</div><h3>El menú se está preparando</h3><p>Agrega productos de muestra desde el panel de administración de Django.</p></div>}
        </section><aside className="cart-card"><div className="cart-head"><div><div className="eyebrow">TU PEDIDO</div><h2>El carrito <span>({cartItems.reduce((s, i) => s + i.quantity, 0)})</span></h2></div><span className="cart-icon">↗</span></div>
          {!cartItems.length ? <div className="cart-empty"><span>＋</span><p>Tu carrito está esperando<br />algo delicioso.</p></div> : <>
            <div className="cart-lines">{cartItems.map(({ product, quantity }) => <div className="cart-line" key={product.id}><div><strong>{product.name}</strong><small>{money(product.price)} c/u</small></div><div className="quantity"><button onClick={() => changeQuantity(String(product.id), -1)} aria-label="Quitar uno">−</button><span>{quantity}</span><button onClick={() => changeQuantity(String(product.id), 1)} aria-label="Agregar uno">+</button></div></div>)}</div>
            <form className="checkout" onSubmit={placeOrder}>{["operator", "admin"].includes(staffRole) && <label>Cliente<select value={customerId} onChange={event => setCustomerId(event.target.value)} required><option value="">Selecciona un cliente</option>{customers.map(item => <option key={item.id} value={item.id}>{item.first_name || item.username} {item.last_name}</option>)}</select></label>}{!['operator', 'admin'].includes(staffRole) && addresses.length > 0 && <label>Direcciones guardadas<select value={addressId} onChange={event => { const value = event.target.value; const saved = addresses.find(item => String(item.id) === value); setAddressId(value); setAddress(saved?.address || ""); setAddressLabel(saved?.label || "Casa") }}><option value="new">Usar una dirección nueva</option>{addresses.map(item => <option key={item.id} value={item.id}>{item.label} · {item.address}</option>)}</select></label>}{!['operator', 'admin'].includes(staffRole) && addressId === "new" && <label>Nombre de la dirección<input value={addressLabel} onChange={event => setAddressLabel(event.target.value)} maxLength="60" /></label>}<label>Dirección de entrega<textarea value={address} onChange={event => { const value = event.target.value; setAddress(value); if (!addresses.some(item => item.address === value)) setAddressId("new") }} placeholder="Calle, número, barrio y referencia" required maxLength="300" /></label>{!['operator', 'admin'].includes(staffRole) && addressId === "new" && <button type="button" className="text-button address-save" onClick={saveAddress}>Guardar dirección para después</button>}<label>Forma de pago<select value={payment} onChange={event => setPayment(event.target.value)}><option value="cash">Efectivo</option><option value="card">Tarjeta (simulada)</option><option value="transfer">Transferencia (simulada)</option></select></label><label>Nota para el restaurante <span className="optional">(opcional)</span><input value={notes} onChange={event => setNotes(event.target.value)} placeholder="Sin cebolla, timbre dañado…" maxLength="500" /></label><div className="totals"><div><span>Subtotal</span><span>{money(subtotal)}</span></div><div><span>Domicilio</span><span>{money(selectedBranch?.delivery_fee)}</span></div><div className="grand-total"><strong>Total</strong><strong>{money(total)}</strong></div></div><button className="button button-accent full" disabled={busy}>{busy ? 'Enviando pedido…' : 'Confirmar pedido'} <span>→</span></button><p className="payment-note">Pago simulado · No ingreses datos de tarjeta</p></form>
          </>}</aside></div>
        {staffRole && staffRole !== 'customer' && <section className="orders-section staff-section"><div className="section-heading compact"><div><div className="eyebrow">OPERACIÓN DE SEDE</div><h2>Pedidos para gestionar</h2></div><div className="staff-tools"><button className="button button-light" onClick={loadOrders}>Actualizar</button>{user?.is_superuser && <a className="button button-dark" href="http://127.0.0.1:8000/admin/" target="_blank" rel="noreferrer">Administrar menú</a>}</div></div>
          {!orders.length ? <div className="orders-empty">No hay pedidos pendientes para mostrar.</div> : <div className="orders-list">{orders.map(order => <article className="order-card" key={`staff-${order.id}`}><div className="order-main"><div><span className="order-id">PEDIDO #{order.id}</span><h3>{order.customer_name || 'Cliente'} · {order.branch_name}</h3><small>{order.delivery_address} · {new Date(order.created_at).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })}</small></div><span className={`status status-${order.status}`}>{order.status_label || order.status}</span></div><div className="order-items">{order.items.map(item => <span key={item.id}>{item.quantity} × {item.product_name}</span>)}</div><div className="staff-order-actions">{(staffActions[order.status] || []).filter(([next]) => staffAllowed[staffRole]?.includes(next)).map(([next, label]) => <button key={next} className={`button ${next === 'cancelled' ? 'button-light' : 'button-dark'}`} onClick={() => updateOrderStatus(order.id, next)}>{label}</button>)}</div></article>)}</div>}
        </section>}
        {staffRole === 'customer' && <section className="orders-section"><div className="section-heading compact"><div><div className="eyebrow">SEGUIMIENTO</div><h2>Tus pedidos</h2></div><button className="button button-light" onClick={loadOrders}>Actualizar</button></div>
          {!orders.length ? <div className="orders-empty">Todavía no tienes pedidos. Cuando confirmes uno, podrás seguirlo desde aquí.</div> : <div className="orders-list">{orders.map(order => <article className="order-card" key={order.id}><div className="order-main"><div><span className="order-id">PEDIDO #{order.id}</span><h3>{order.branch_name}</h3><small>{new Date(order.created_at).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })}</small></div><span className={`status status-${order.status}`}>{order.status_label || order.status}</span></div><div className="order-items">{order.items.map(item => <span key={item.id}>{item.quantity} × {item.product_name}</span>)}</div><div className="order-foot"><span>{order.delivery_address}</span><strong>{money(order.total)}</strong></div>{order.status === "received" && staffRole === "customer" && <button className="text-button order-cancel" onClick={() => cancelOrder(order.id)}>Cancelar pedido</button>}</article>)}</div>}
        </section>}
      </>}
    </main>
    <footer><span className="brand"><span className="brand-mark small">D</span>DomiPedidos<span className="brand-x">X</span></span><span>Un pedido bien hecho cambia el día.</span><span>© 2026 DomiPedidosX</span></footer>
    {notice && <div className="toast">✓ {notice}</div>}
  </div>
}
export default App




