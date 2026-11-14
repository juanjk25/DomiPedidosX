import { useMemo, useState } from 'react'
import ImagenProducto from '../components/ImagenProducto.jsx'

const MenuPromociones = ({ products, categories, cartItems, onAdd, onChangeQuantity, onCheckout, onLogout, address, onAddressChange, error, onError, checkingOut, branchName }) => {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('all')

  const filteredProducts = useMemo(() => products.filter(product => {
    const matchesQuery = product.name.toLowerCase().includes(query.toLowerCase())
    const matchesCategory = category === 'all' || product.category_name === category
    return matchesQuery && matchesCategory
  }), [products, query, category])

  return <section className="menu-page">
    <aside className="menu-sidebar">
      <div className="menu-sidebar-brand"><span className="brand-mark">D</span>DomiPedidos<span className="brand-x">X</span></div>
      <span className="menu-sidebar-label">02 / CLIENTE</span>
      <button className="menu-nav active">⌁ <span>Pedir pedido</span></button>
      <button className="menu-nav">▤ <span>Mis pedidos</span></button>
      <button className="menu-nav">♙ <span>Mi cuenta</span></button>
      <div className="menu-sidebar-info">
        <strong>{branchName || 'Selecciona una sede'}</strong>
        
        <p>Tu pizza favorita, donde estés.</p>
      </div>
      <button className="menu-logout" onClick={onLogout}>Cerrar sesión</button>
    </aside>

    <div className="menu-main">
      <div className="menu-page-top"><span>02 / CLIENTE · MENÚ</span></div>
      <div className="menu-heading"><div><h1>¿Qué se te antoja hoy?</h1><p>Recién hecha, a tu gusto y hasta tu puerta.</p></div><span className="menu-user">Hola, cliente · ¿Necesitas ayuda?</span></div>
      <div className="menu-delivery"><strong>Entregar en Casa</strong><span>{address || 'Indica tu dirección de entrega'}</span><b>{branchName || 'Selecciona una sede'}</b></div>
      <div className="menu-content-grid">
        <div>
          <div className="menu-promo-hero"><div><span>RECIÉN HECHA. CERCA DE TI.</span><h2>Una buena pizza cambia tu día.</h2><p>Masa artesanal y tus ingredientes favoritos.</p></div><div className="menu-pizza-art">🍕</div></div>
          <h2 className="menu-section-title">Menú de la sede</h2>
          <input aria-label="Buscar por nombre de producto" className="menu-search" value={query} onChange={event => setQuery(event.target.value)} placeholder="⌕  Buscar por nombre de producto" />
          <div className="menu-filters"><button className={category === 'all' ? 'selected' : ''} onClick={() => setCategory('all')}>Todo</button>{categories.map(item => <button key={item.id} className={category === item.name ? 'selected' : ''} onClick={() => setCategory(item.name)}>{item.name}</button>)}</div>
          <div className="menu-results">{filteredProducts.length} productos · Filtra según tu búsqueda</div>
          {!filteredProducts.length && <p role="status">No hay productos disponibles con estos filtros.</p>}
          <div className="menu-products">{filteredProducts.map(product => <article key={product.id}><div className="menu-product-image"><ImagenProducto src={product.image} name={product.name} /></div><div><h3>{product.name}</h3><p>{product.description}</p><strong>{new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(Number(product.price || 0))}</strong><button aria-label={`Agregar ${product.name}`} onClick={() => onAdd(product)}>＋</button></div></article>)}</div>
        </div>
        <aside className="menu-order-summary"><h2>Mi pedido · {cartItems.reduce((sum, item) => sum + item.quantity, 0)} unidades</h2>{cartItems.length ? cartItems.map(item => <div className="menu-order-line" key={item.product.id}><div><span>{item.product.name}</span><small>{new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(Number(item.product.price || 0))} c/u</small><div className="menu-quantity"><button aria-label={`Quitar una unidad de ${item.product.name}`} onClick={() => onChangeQuantity(item.product.id, -1)}>−</button><strong>{item.quantity}</strong><button aria-label={`Agregar una unidad de ${item.product.name}`} onClick={() => onChangeQuantity(item.product.id, 1)}>+</button><button className="menu-remove" aria-label={`Eliminar ${item.product.name}`} onClick={() => onChangeQuantity(item.product.id, -item.quantity)}>Quitar</button></div></div><strong>{new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(Number(item.product.price || 0) * item.quantity)}</strong></div>) : <p className="menu-empty-order">Aún no has agregado productos.</p>}<div className="menu-order-address"><strong>Casa · Dirección principal</strong><input aria-label="Dirección de entrega" value={address} onChange={event => onAddressChange(event.target.value)} placeholder="Calle 85 # 15-20" /></div>{error && <p className="error-message">{error}<button className="clear-error" onClick={() => onError('')}>×</button></p>}<button className="primary-button full" onClick={onCheckout} disabled={checkingOut}>{checkingOut ? 'Confirmando…' : 'Continuar pedido →'}</button></aside>
      </div>
    </div>
  </section>
}

export default MenuPromociones
