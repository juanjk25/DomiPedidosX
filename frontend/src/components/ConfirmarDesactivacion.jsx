import { useEffect, useRef } from 'react'
export default function ConfirmarDesactivacion({ product, busy, error, onConfirm, onCancel }) {
  const dialog = useRef(null)
  useEffect(() => { const node = dialog.current; node.showModal(); return () => node.close() }, [])
  return <dialog ref={dialog} className="confirmation-dialog" aria-labelledby="disable-title" aria-describedby="disable-description" onCancel={e => { e.preventDefault(); if (!busy) onCancel() }}>
    <h2 id="disable-title">¿Desactivar producto?</h2>
    <p id="disable-description"><strong>{product.nombre_producto}</strong> dejará de aparecer en el menú del cliente. Sus datos se conservarán y podrás volver a publicarlo.</p>
    {error && <p className="error-message" role="alert">{error}</p>}
    <div className="form-actions"><button autoFocus className="secondary-button" onClick={onCancel} disabled={busy}>Cancelar</button><button className="primary-button" onClick={onConfirm} disabled={busy}>{busy ? 'Desactivando…' : 'Confirmar desactivación'}</button></div>
  </dialog>
}
