import { useState } from 'react'
export default function ImagenProducto({ src, name }) {
  const [failedSrc, setFailedSrc] = useState(null)
  return src && failedSrc !== src
    ? <img className="product-photo" src={src} alt={name} loading="lazy" referrerPolicy="no-referrer" onError={() => setFailedSrc(src)} />
    : <span className="product-photo-placeholder" role="img" aria-label={`Sin imagen disponible para ${name}`}>🍽️</span>
}
