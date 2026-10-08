import { spawn, spawnSync } from 'node:child_process'

const migration = spawnSync('python', ['manage.py', 'migrate'], {
  cwd: '/app/backend',
  stdio: 'inherit',
})

if (migration.error) throw migration.error
if (migration.status !== 0) process.exit(migration.status ?? 1)

const services = [
  spawn('python', ['manage.py', 'runserver', '0.0.0.0:8000'], {
    cwd: '/app/backend',
    stdio: 'inherit',
  }),
  spawn('npm', ['run', 'dev', '--', '--host', '0.0.0.0'], {
    cwd: '/app/frontend',
    stdio: 'inherit',
  }),
]

let stopping = false

function stop(exitCode = 0) {
  if (stopping) return
  stopping = true
  for (const service of services) {
    if (service.exitCode === null) service.kill('SIGTERM')
  }
  const forceExit = setTimeout(() => process.exit(exitCode), 3000)
  forceExit.unref()
}

for (const service of services) {
  service.on('error', error => {
    console.error('No se pudo iniciar un servicio:', error)
    stop(1)
  })
  service.on('exit', (code, signal) => {
    if (!stopping) {
      console.error(`Un servicio terminó (${signal ?? code}); deteniendo el contenedor.`)
      stop(code ?? 1)
    }
  })
}

process.on('SIGINT', () => stop(0))
process.on('SIGTERM', () => stop(0))
