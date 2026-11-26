param(
    [string]$ApiUrl = "http://localhost:8000/api/pedidos/cocina/",
    [int]$IntervalSeconds = 5
)

$token = $env:DOMI_ACCESS_TOKEN

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Error "Define DOMI_ACCESS_TOKEN con el access token de un usuario de cocina."
    exit 1
}

if ($IntervalSeconds -lt 1) {
    Write-Error "IntervalSeconds debe ser al menos 1 segundo."
    exit 1
}

$headers = @{
    Authorization = "Bearer $token"
}

Write-Host "Consultando $ApiUrl cada $IntervalSeconds segundos. Ctrl+C para detener."

while ($true) {
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-RestMethod `
            -Method Get `
            -Uri $ApiUrl `
            -Headers $headers
        $stopwatch.Stop()

        Write-Host ""
        Write-Host (
            "Actualización: {0} | respuesta: {1} ms" -f
            (Get-Date -Format "yyyy-MM-dd HH:mm:ss"),
            $stopwatch.ElapsedMilliseconds
        )

        $response.pedidos_por_estado | ConvertTo-Json -Depth 8
    }
    catch {
        Write-Warning ("No se pudo consultar la cola: {0}" -f $_.Exception.Message)
    }

    Start-Sleep -Seconds $IntervalSeconds
}