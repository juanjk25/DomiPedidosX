import test, { beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { api, saveTokens } from '../../src/api.js'
beforeEach(() => { const store = new Map(); global.localStorage = { getItem: key => store.get(key) || null, setItem: (key, value) => store.set(key, value), removeItem: key => store.delete(key) } })
test('A4: agrega autorización solo en peticiones autenticadas', async () => {
  saveTokens({ access: 'access', refresh: 'refresh' })
  const requests = []
  global.fetch = async (url, options) => { requests.push(options); return new Response('{}') }
  await api('/me/'); await api('/auth/password-reset/', { auth: false })
  assert.equal(requests[0].headers.Authorization, 'Bearer access')
  assert.equal(requests[1].headers.Authorization, undefined)
})
test('A4: renueva access token y repite una vez', async () => {
  saveTokens({ access: 'old', refresh: 'refresh' }); let count = 0
  global.fetch = async url => { count++; return url.endsWith('/refresh/') ? new Response('{"access":"new"}') : new Response(count === 1 ? '{}' : '{"id":1}', { status: count === 1 ? 401 : 200 }) }
  assert.deepEqual(await api('/me/'), { id: 1 }); assert.equal(localStorage.getItem('domi_access'), 'new'); assert.equal(count, 3)
})
test('A4: una renovación fallida elimina la sesión', async () => {
  saveTokens({ access: 'old', refresh: 'expired' }); global.fetch = async () => new Response('{}', { status: 401 })
  await assert.rejects(api('/me/')); assert.equal(localStorage.getItem('domi_access'), null)
})
test('A6/B5: conserva errores de campos y muestra fallo de red', async () => {
  global.fetch = async () => new Response('{"nombre_producto":["Obligatorio"]}', { status: 400 })
  await assert.rejects(api('/management/products/'), err => err.fields.nombre_producto[0] === 'Obligatorio')
  global.fetch = async () => { throw new TypeError('network') }
  await assert.rejects(api('/auth/password-reset/', { auth: false }), /conectar con el servidor/)
})
