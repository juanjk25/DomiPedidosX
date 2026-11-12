import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, clearSession, getToken } from './api.js'
import RegistroPanel from './components/RegistroPanel.jsx'
import IniciarSesion from './pages/IniciarSesion.jsx'
import RecuperarContrasena from './pages/RecuperarContrasena.jsx'
import RestablecerContrasena from './pages/RestablecerContrasena.jsx'
import GestionMenu from './pages/GestionMenu.jsx'
import MenuPromociones from './pages/MenuPromociones.jsx'
import InicioPersonal from './pages/InicioPersonal.jsx'
import { homeFor } from './utils/session.js'
import './sprint1.css'

export default function App() {
  const [path, setPath] = useState(window.location.pathname)
  const [user, setUser] = useState(null), [restoring, setRestoring] = useState(!!getToken()), [sessionNotice, setSessionNotice] = useState('')
  const [products, setProducts] = useState([]), [categories, setCategories] = useState([]), [branches, setBranches] = useState([]), [branch, setBranch] = useState('')
  const [cart, setCart] = useState({}), [address, setAddress] = useState(''), [error, setError] = useState(''), [notice, setNotice] = useState(''), [checkingOut, setCheckingOut] = useState(false)
  const navigate = useCallback(next => { window.history.pushState({}, '', next); setPath(next); window.scrollTo(0, 0) }, [])
  useEffect(() => {
    const back = () => setPath(window.location.pathname)
    const expired = () => { setUser(null); setCart({}); setSessionNotice('Tu sesión venció. Inicia sesión nuevamente.'); navigate('/login') }
    window.addEventListener('popstate', back); window.addEventListener('domi:session-expired', expired)
    return () => { window.removeEventListener('popstate', back); window.removeEventListener('domi:session-expired', expired) }
  }, [navigate])
  useEffect(() => {
    if (!getToken()) return
    let current = true
    api('/me/').then(profile => { if (current) { setUser(profile); setAddress(profile.direccion_residencia || '') } })
      .catch(() => { if (current) { clearSession(); setSessionNotice('No pudimos recuperar tu sesión. Inicia sesión nuevamente.') } })
      .finally(() => { if (current) setRestoring(false) })
    return () => { current = false }
  }, [])
  async function authenticated() {
    const profile = await api('/me/')
    setUser(profile); setAddress(profile.direccion_residencia || ''); setSessionNotice(''); setError('')
    navigate(homeFor(profile))
  }
  const viewingMenu = !!user && (user.role === 'customer' || user.can_manage_menu) && path !== '/recuperar-contrasena' && path !== '/restablecer-contrasena' && !(user.can_manage_menu && path !== '/menu')
  useEffect(() => {
    if (!viewingMenu) return
    const controller = new AbortController()
    api('/branches/', { auth: false, signal: controller.signal }).then(data => { setBranches(data); setBranch(old => old || String(data[0]?.id_sede || '')) })
      .catch(err => { if (err.name !== 'AbortError') setError(err.message) })
    return () => controller.abort()
  }, [viewingMenu])
  useEffect(() => {
    if (!viewingMenu || !branch) return
    let current = true
    const controller = new AbortController()
    async function reload() {
      try {
        const [categoryData, productData] = await Promise.all([api(`/categories/?sede=${branch}`, { auth: false, signal: controller.signal }), api(`/products/?sede=${branch}`, { auth: false, signal: controller.signal })])
        if (!current) return
        setCategories(categoryData.map(item => ({ id: item.id, name: item.nombre })))
        setProducts(productData.map(item => ({ id: item.id_producto, name: item.nombre_producto, price: item.precio_venta, category_name: item.tipo_de_producto, description: item.tiempo_preparacion ? `${item.tiempo_preparacion} min de preparación` : '', image: item.imagen_url })))
        const ids = new Set(productData.map(item => String(item.id_producto)))
        setCart(old => Object.fromEntries(Object.entries(old).filter(([id]) => ids.has(id))))
      } catch (err) { if (current && err.name !== 'AbortError') setError(err.message) }
    }
    const onStorage = event => { if (event.key === 'domi_menu_revision') reload() }
    reload()
    const interval = setInterval(reload, 15000)
    window.addEventListener('focus', reload); window.addEventListener('storage', onStorage); window.addEventListener('domi:menu-updated', reload)
    return () => { current = false; controller.abort(); clearInterval(interval); window.removeEventListener('focus', reload); window.removeEventListener('storage', onStorage); window.removeEventListener('domi:menu-updated', reload) }
  }, [viewingMenu, branch])
  useEffect(() => { if (!notice) return; const timer = setTimeout(() => setNotice(''), 3500); return () => clearTimeout(timer) }, [notice])
  const cartItems = useMemo(() => Object.entries(cart).map(([id, quantity]) => ({ product: products.find(item => String(item.id) === id), quantity })).filter(item => item.product), [cart, products])
  function addProduct(product) { setCart(old => ({ ...old, [product.id]: Math.min((old[product.id] || 0) + 1, 20) })); setNotice(`${product.name} agregado al pedido`) }
  function changeQuantity(id, delta) { setCart(old => { const next = { ...old }; const quantity = Math.min((next[id] || 0) + delta, 20); if (quantity <= 0) delete next[id]; else next[id] = quantity; return next }) }
  function logout() { clearSession(); setUser(null); setCart({}); setProducts([]); setSessionNotice(''); navigate('/login') }
  async function checkout() {
    if (checkingOut) return
    if (!cartItems.length) { setError('Agrega al menos un producto al pedido.'); return }
    if (!address.trim()) { setError('Escribe una dirección de entrega.'); return }
    setError(''); setCheckingOut(true)
    try {
      await api('/orders/', { method: 'POST', body: JSON.stringify({ sede: Number(branch), direccion_entrega: address.trim(), items: cartItems.map(item => ({ producto_id: item.product.id, cantidad: item.quantity })) }) })
      setCart({}); setNotice('Pedido confirmado correctamente')
    } catch (err) { setError(err.message) }
    finally { setCheckingOut(false) }
  }
  let content
  if (path === '/recuperar-contrasena') content = <RecuperarContrasena navigate={navigate} />
  else if (path === '/restablecer-contrasena') content = <RestablecerContrasena navigate={navigate} onReset={() => setUser(null)} />
  else if (restoring) content = <p className="session-loading" role="status">Recuperando sesión…</p>
  else if (!user) content = path === '/registro' ? <RegistroPanel onAuthenticated={authenticated} navigate={navigate} /> : <IniciarSesion onAuthenticated={authenticated} navigate={navigate} notice={sessionNotice} />
  else if (user.role !== 'customer' && !user.can_manage_menu) content = <InicioPersonal user={user} onLogout={logout} />
  else if (user.can_manage_menu && path !== '/menu') content = <GestionMenu onPreview={() => navigate('/menu')} onLogout={logout} />
  else content = <>
    <div className="customer-toolbar"><label>Sede<select aria-label="Sede del menú" value={branch} onChange={e => { setBranch(e.target.value); setCart({}); setProducts([]); setError('') }}><option value="" disabled>Selecciona una sede</option>{branches.map(b => <option key={b.id_sede} value={b.id_sede}>{b.nombre_sede}</option>)}</select></label>{user.can_manage_menu && <button className="secondary-button" onClick={() => navigate('/gestion-menu')}>Volver a gestionar menú</button>}<button className="secondary-button" onClick={logout}>Cerrar sesión</button></div>
    <MenuPromociones products={products} categories={categories} cartItems={cartItems} address={address} error={error} onError={setError} onAddressChange={setAddress} onAdd={addProduct} onChangeQuantity={changeQuantity} onCheckout={checkout} onLogout={logout} checkingOut={checkingOut} branchName={branches.find(b => String(b.id_sede) === branch)?.nombre_sede} />
  </>
  return <div className="app-shell">{content}{notice && <div className="toast" role="status">✓ {notice}</div>}</div>
}
