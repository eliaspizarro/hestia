# Crear archivo de log con marca de tiempo
$logFile = "test_results_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$server = "192.168.228.130:5000"
$token = "prueba-token"
$zoneId = "test-zone-id"
$recordId = "test-record-id"

# Función para escribir en consola y archivo
function Write-Log {
    param([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    # Filtrar líneas que contienen System.Management.Automation.RemoteException
    $filteredMessage = $message -split "`n" | Where-Object { $_ -notmatch "System\.Management\.Automation\.RemoteException" } | Out-String
    $logMessage = "[$timestamp] $filteredMessage"
    Write-Host $logMessage
    Add-Content -Path $logFile -Value $logMessage
}

Write-Log "Iniciando pruebas contra servidor: $server"
Write-Log "----------------------------------------"

# 1. Probar endpoint de IP
Write-Log "`n1. Probando /ip:"
$result = curl.exe -s -v "http://$server/ip" 2>&1
Write-Log ($result -join "`n")

# 2. Listar zonas (sin autenticación - debería fallar)
Write-Log "`n2. Probando listar zonas SIN autenticación:"
$result = curl.exe -s -v "http://$server/client/v4/zones" 2>&1
Write-Log ($result -join "`n")

# 3. Listar zonas (con autenticación)
Write-Log "`n3. Probando listar zonas CON autenticación:"
$result = curl.exe -s -v -H "Authorization: Bearer $token" "http://$server/client/v4/zones" 2>&1
Write-Log ($result -join "`n")

# 4. Listar registros DNS
Write-Log "`n4. Probando listar registros DNS:"
$result = curl.exe -s -v -H "Authorization: Bearer $token" "http://$server/client/v4/zones/$zoneId/dns_records" 2>&1
Write-Log ($result -join "`n")

# 4.1 Obtener zona existente
$existingZoneId = "eee3864538734cd57fecd8eaa51a91bb"  # ID de la zona de prueba existente
Write-Log "`n4.1 Probando obtener zona existente (ID: $existingZoneId):"
$result = curl.exe -s -v -H "Authorization: Bearer $token" "http://$server/client/v4/zones/$existingZoneId" 2>&1
Write-Log ($result -join "`n")

# 4.2 Obtener zona con ID con formato inválido (demasiado corto)
$invalidZoneId = "123"
Write-Log "`n4.2 Probando obtener zona con ID inválido (demasiado corto):"
$result = curl.exe -s -v -H "Authorization: Bearer $token" "http://$server/client/v4/zones/$invalidZoneId" 2>&1
Write-Log ($result -join "`n")

# 4.3 Obtener zona que no existe
$nonExistentZoneId = "1234567890abcdef1234567890abcdef"
Write-Log "`n4.3 Probando obtener zona que no existe (ID: $nonExistentZoneId):"
$result = curl.exe -s -v -H "Authorization: Bearer $token" "http://$server/client/v4/zones/$nonExistentZoneId" 2>&1
Write-Log ($result -join "`n")

# 4.4 Obtener zona sin autenticación
Write-Log "`n4.4 Probando obtener zona sin autenticación:"
$result = curl.exe -s -v "http://$server/client/v4/zones/$existingZoneId" 2>&1
Write-Log ($result -join "`n")

# 5. Probar método no permitido
Write-Log "`n5. Probando método no permitido (DELETE /ip):"
$result = curl.exe -s -v -X DELETE "http://$server/ip" 2>&1
Write-Log ($result -join "`n")

# 6. Probar endpoint inexistente
Write-Log "`n6. Probando endpoint inexistente:"
$result = curl.exe -s -v "http://$server/endpoint-inexistente" 2>&1
Write-Log ($result -join "`n")

# 7. Probar actualización de registro DNS
Write-Log "`n7. Probando actualización de registro DNS:"
$body = @{
    type = "A"
    name = "ejemplo.com"
    content = "192.168.1.1"
    ttl = 120
    proxied = $false
} | ConvertTo-Json -Compress

# Guardar el JSON en un archivo temporal para evitar problemas de comillas
$tempFile = [System.IO.Path]::GetTempFileName()
$body | Out-File -FilePath $tempFile -Encoding utf8

$result = curl.exe -s -v -X PUT `
    -H "Authorization: Bearer $token" `
    -H "Content-Type: application/json" `
    --data-binary "@$tempFile" `
    "http://$server/client/v4/zones/$zoneId/dns_records/$recordId" 2>&1

# Eliminar el archivo temporal
Remove-Item -Path $tempFile -Force

Write-Log ($result -join "`n")

# 8. Probar JSON mal formado
Write-Log "`n8. Probando con JSON mal formado:"
$malformedJson = '{"malformed": "json'
$tempFile = [System.IO.Path]::GetTempFileName()
$malformedJson | Out-File -FilePath $tempFile -Encoding utf8

$result = curl.exe -s -v -X POST `
    -H "Authorization: Bearer $token" `
    -H "Content-Type: application/json" `
    --data-binary "@$tempFile" `
    "http://$server/client/v4/zones/$zoneId/dns_records" 2>&1

# Eliminar el archivo temporal
Remove-Item -Path $tempFile -Force

Write-Log ($result -join "`n")

Write-Log "`nPruebas completadas. Resultados guardados en: $((Get-Item $logFile).FullName)"
Write-Host "`n¡Pruebas completadas! Revisa el archivo: $((Get-Item $logFile).FullName)" -ForegroundColor Green