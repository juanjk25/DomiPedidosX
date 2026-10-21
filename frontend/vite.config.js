import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({ 
    plugins: [react(), tailwindcss()], 
    server: { 
        host: '0.0.0.0', 
        port: 5173,
        watch: {
            usePolling: true,      // 🔄 Fuerza a Vite a revisar los archivos constantemente
            interval: 1000,        // Revisa cada 1 segundo (opcional, ayuda si va lento)
        }
    } 
})