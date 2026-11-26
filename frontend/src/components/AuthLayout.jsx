export default function AuthLayout({ title, description, children }) {
  return <section className="login-page">
    <div className="login-brand"><span className="brand-mark">D</span><strong>DomiPedidos<span className="brand-x">X</span></strong></div>
    <div className="login-card">
      <span className="login-kicker">CUENTA DOMIPEDIDOS</span>
      <h1>{title}</h1><p>{description}</p>{children}
    </div>
  </section>
}
