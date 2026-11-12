import test from 'node:test'
import assert from 'node:assert/strict'
import { productPayload, validateProduct, visibleProducts } from '../../src/utils/productos.js'
const valid = { nombre_producto: 'Pizza', codigo_de_barras: '001', categoria: '1', sede: '1', imagen_url: 'https://example.org/pizza.jpg', tiempo_preparacion: '15', precio_venta: '20000.50', precio_compra: '0', activo: true }
test('B5: producto válido y conversión de tipos', () => {
  assert.deepEqual(validateProduct(valid), {})
  assert.equal(productPayload({ ...valid, nombre_producto: ' Pizza ' }).nombre_producto, 'Pizza')
  assert.equal(productPayload(valid).sede, 1)
  assert.equal(productPayload(valid).tiempo_preparacion, 15)
})
test('B5/B6: detecta obligatorios vacíos', () => {
  for (const name of ['nombre_producto', 'codigo_de_barras', 'categoria', 'sede', 'imagen_url', 'tiempo_preparacion', 'precio_venta']) assert.ok(validateProduct({ ...valid, [name]: ' ' })[name], name)
})
test('B5/B6: precios, decimales, minutos y URL inválidos', () => {
  for (const [name, values] of Object.entries({ precio_venta: ['0', '-1', 'NaN', '2.555', '1e5'], precio_compra: ['-1', ''], tiempo_preparacion: ['0', '1441', '1.5'], imagen_url: ['javascript:alert(1)', 'ftp://example.org/x', 'texto'] }))
    for (const value of values) assert.ok(validateProduct({ ...valid, [name]: value })[name], `${name}: ${value}`)
})
test('B8: los inactivos se conservan en gestión y se filtran por estado', () => {
  const products = [{ nombre_producto: 'Pizza', activo: false }, { nombre_producto: 'Limonada', activo: true }]
  assert.equal(visibleProducts(products).length, 2)
  assert.deepEqual(visibleProducts(products, '', 'active'), [products[1]])
  assert.deepEqual(visibleProducts(products, ' PIZZA ', 'inactive'), [products[0]])
})
