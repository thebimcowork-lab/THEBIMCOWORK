#Requires -Version 5.1
<#
.SYNOPSIS
    Instalador de revit-mcp para el curso MCP + Claude (The BIM Co-Work).

.DESCRIPTION
    Deja funcionando en un solo paso la cadena completa:
      Claude  <--stdio-->  MCP Server (Node)  <--WebSocket-->  Add-in de Revit  -->  Revit API

    Hace, en orden:
      1. Detecta las versiones de Revit instaladas.
      2. Descarga el add-in oficial (release de mcp-servers-for-revit) para cada version.
      3. Lo copia a %AppData%\Autodesk\Revit\Addins\<anio>\
      4. Verifica / instala Node.js 18+ (via winget).
      5. Registra el servidor MCP en Claude Code y en Claude Desktop.
      6. Verifica que todo quedo en su lugar e imprime los pasos manuales que faltan.

.PARAMETER RevitVersions
    Anios de Revit a instalar (ej: -RevitVersions 2024,2025). Por defecto: todos los detectados.

.PARAMETER SoloVerificar
    No instala nada: solo diagnostica el estado del equipo.

.PARAMETER OmitirNode
    No intenta instalar Node.js aunque falte (util en equipos sin permisos de administrador).

.EXAMPLE
    .\install.ps1

.EXAMPLE
    .\install.ps1 -SoloVerificar

.EXAMPLE
    .\install.ps1 -RevitVersions 2024
#>
[CmdletBinding()]
param(
    [int[]]$RevitVersions,
    [switch]$SoloVerificar,
    [switch]$OmitirNode
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# ---------------------------------------------------------------- constantes
$RepoAddin       = 'mcp-servers-for-revit/mcp-servers-for-revit'
$TagPorDefecto   = 'v1.0.0'
$PaqueteNpm      = 'mcp-server-for-revit'
$NombreServidor  = 'revit-mcp'
$AniosSoportados = 2020..2026

$script:Errores      = @()
$script:Advertencias = @()

# ---------------------------------------------------------------- utilidades
function Write-Titulo { param($t) Write-Host ''; Write-Host "== $t" -ForegroundColor Cyan }
function Write-Paso   { param($t) Write-Host "   $t" }
function Write-Ok     { param($t) Write-Host "   [OK]   $t" -ForegroundColor Green }
function Write-Aviso  { param($t) Write-Host "   [!]    $t" -ForegroundColor Yellow; $script:Advertencias += $t }
function Write-Falla  { param($t) Write-Host "   [ERR]  $t" -ForegroundColor Red;    $script:Errores += $t }

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    return (New-Object Security.Principal.WindowsPrincipal($id)).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Update-PathDeSesion {
    $m = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $u = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = ($m, $u | Where-Object { $_ }) -join ';'
}

function Get-RutaComando {
    param([string]$Nombre)
    $c = Get-Command $Nombre -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    return $null
}

function Get-NodeMajor {
    Update-PathDeSesion
    if (-not (Get-RutaComando 'node')) { return -1 }
    try {
        $v = (& node -v) -replace '^v', ''
        return [int]($v.Split('.')[0])
    } catch { return -1 }
}

# ---------------------------------------------------------------- 0. entorno
Write-Host ''
Write-Host '  +--------------------------------------------------------+' -ForegroundColor White
Write-Host '  |  revit-mcp  ::  instalador del curso MCP + Claude       |' -ForegroundColor White
Write-Host '  |  The BIM Co-Work / Metodo TBC                           |' -ForegroundColor White
Write-Host '  +--------------------------------------------------------+' -ForegroundColor White

Write-Titulo 'Entorno'
Write-Paso "Windows      : $([Environment]::OSVersion.Version)"
Write-Paso "PowerShell   : $($PSVersionTable.PSVersion)"
Write-Paso "Usuario      : $env:USERNAME"
if (Test-Admin) { Write-Paso 'Privilegios  : administrador' }
else            { Write-Paso 'Privilegios  : usuario normal (suficiente)' }
if ($SoloVerificar) { Write-Host '   MODO DIAGNOSTICO: no se modificara nada.' -ForegroundColor Magenta }

# ---------------------------------------------------------------- 1. Revit
Write-Titulo '1. Revit instalado'

$revitDetectado = @()
foreach ($anio in $AniosSoportados) {
    $exe = Join-Path $env:ProgramFiles "Autodesk\Revit $anio\Revit.exe"
    if (Test-Path $exe) { $revitDetectado += $anio }
}

if ($revitDetectado.Count -eq 0) {
    Write-Aviso 'No se detecto ninguna instalacion de Revit 2020-2026 en C:\Program Files\Autodesk.'
    Write-Paso  'Si Revit esta en otra ruta, indica la version a mano:  .\install.ps1 -RevitVersions 2024'
} else {
    Write-Ok "Revit detectado: $($revitDetectado -join ', ')"
}

if ($RevitVersions) {
    $aniosObjetivo = @($RevitVersions | Where-Object { $AniosSoportados -contains $_ })
    foreach ($r in @($RevitVersions | Where-Object { $AniosSoportados -notcontains $_ })) {
        Write-Aviso "Revit $r no esta soportado por el add-in (solo 2020-2026)."
    }
} else {
    $aniosObjetivo = $revitDetectado
}

if ($aniosObjetivo.Count -eq 0 -and -not $SoloVerificar) {
    Write-Falla 'Sin versiones de Revit sobre las que instalar. Instala Revit y vuelve a ejecutar.'
}

if (Get-Process -Name 'Revit' -ErrorAction SilentlyContinue) {
    Write-Aviso 'Revit esta ABIERTO. Cierralo o los archivos del add-in quedaran bloqueados.'
    if (-not $SoloVerificar) {
        $r = Read-Host '   Cierra Revit y presiona ENTER para seguir (o escribe N para abortar)'
        if ($r -match '^[nN]') { Write-Host '   Abortado por el usuario.'; exit 1 }
    }
}

# ---------------------------------------------------------------- 2. add-in
Write-Titulo '2. Add-in de Revit (release oficial)'

$tag = $TagPorDefecto
try {
    $rel = Invoke-RestMethod "https://api.github.com/repos/$RepoAddin/releases/latest" `
                             -Headers @{ 'User-Agent' = 'revit-mcp-setup' } -TimeoutSec 20
    if ($rel.tag_name) { $tag = $rel.tag_name }
    Write-Ok "Ultima version publicada: $tag"
} catch {
    Write-Aviso "No se pudo consultar GitHub; se usara la version fija $tag."
}

$carpetaAddins = Join-Path $env:APPDATA 'Autodesk\Revit\Addins'
$tmp = Join-Path $env:TEMP ('revit-mcp-' + [guid]::NewGuid().ToString('N').Substring(0, 8))

foreach ($anio in $aniosObjetivo) {

    $destino = Join-Path $carpetaAddins "$anio"
    $addinYaEsta = @(Get-ChildItem $destino -Filter '*.addin' -File -ErrorAction SilentlyContinue |
                     Where-Object { $_.Name -like '*mcp*' }).Count -gt 0

    if ($SoloVerificar) {
        if ($addinYaEsta) { Write-Ok    "Revit $anio : add-in presente en $destino" }
        else              { Write-Aviso "Revit $anio : add-in NO instalado." }
        continue
    }

    if ($addinYaEsta) { Write-Paso "Revit $anio : add-in ya presente, se reinstala en $tag" }

    $zipNombre = "mcp-servers-for-revit-$tag-Revit$anio.zip"
    $url = "https://github.com/$RepoAddin/releases/download/$tag/$zipNombre"
    $zip = Join-Path $tmp $zipNombre
    $ext = Join-Path $tmp "x$anio"

    try {
        New-Item -ItemType Directory -Path $tmp -Force | Out-Null
        Write-Paso "Revit $anio : descargando $zipNombre ..."
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing -TimeoutSec 300

        $mb = [math]::Round((Get-Item $zip).Length / 1MB, 1)
        Write-Paso "Revit $anio : descargado ($mb MB), extrayendo ..."
        Expand-Archive -Path $zip -DestinationPath $ext -Force

        # el zip puede traer el contenido en la raiz o dentro de una sola carpeta
        $raiz = $ext
        $hayAddin = @(Get-ChildItem $raiz -Filter '*.addin' -File -ErrorAction SilentlyContinue).Count -gt 0
        if (-not $hayAddin) {
            $sub = @(Get-ChildItem $raiz -Directory)
            if ($sub.Count -eq 1) { $raiz = $sub[0].FullName }
        }

        New-Item -ItemType Directory -Path $destino -Force | Out-Null
        Copy-Item -Path (Join-Path $raiz '*') -Destination $destino -Recurse -Force

        $addinFinal = @(Get-ChildItem $destino -Filter '*.addin' -File -ErrorAction SilentlyContinue |
                        Where-Object { $_.Name -like '*mcp*' })
        if ($addinFinal.Count -gt 0) {
            Write-Ok "Revit $anio : $($addinFinal[0].Name) instalado en $destino"
        } else {
            Write-Falla "Revit $anio : la copia termino pero no aparece el .addin en $destino"
        }
    }
    catch {
        Write-Falla "Revit $anio : fallo la instalacion del add-in -> $($_.Exception.Message)"
    }
}

if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }

# ---------------------------------------------------------------- 3. Node.js
Write-Titulo '3. Node.js (motor del servidor MCP)'

$major = Get-NodeMajor

if ($major -ge 18) {
    Write-Ok "Node.js $(& node -v) detectado."
}
elseif ($SoloVerificar) {
    Write-Aviso 'Node.js 18+ no esta disponible en el PATH.'
}
elseif ($OmitirNode) {
    Write-Aviso 'Node.js falta, pero se pidio omitir su instalacion (-OmitirNode).'
}
else {
    if ($major -ge 0) { Write-Aviso "Node.js v$major es demasiado antiguo (se necesita 18+). Se actualiza." }
    else              { Write-Paso  'Node.js no encontrado. Instalando LTS con winget ...' }

    if (Get-RutaComando 'winget') {
        try {
            & winget install --id OpenJS.NodeJS.LTS --exact --silent `
                             --accept-package-agreements --accept-source-agreements | Out-Null
            $major = Get-NodeMajor
            if ($major -ge 18) {
                Write-Ok "Node.js $(& node -v) instalado."
            } else {
                Write-Aviso 'winget termino pero Node no aparece en el PATH: cierra y reabre la terminal.'
            }
        } catch {
            Write-Falla "winget no pudo instalar Node.js -> $($_.Exception.Message)"
        }
    } else {
        Write-Falla 'winget no esta disponible. Instala Node.js LTS desde https://nodejs.org y repite.'
    }
}

# ---------------------------------------------------------------- 4. clientes
Write-Titulo '4. Registro del servidor MCP en Claude'

$comando = 'cmd'
$argsMcp = @('/c', 'npx', '-y', $PaqueteNpm)

# ---- 4a. Claude Code (CLI)
$claudeCli = Get-RutaComando 'claude'

if ($SoloVerificar) {
    if ($claudeCli) { Write-Ok "Claude Code CLI detectado: $claudeCli" }
    else            { Write-Aviso 'Claude Code CLI no esta en el PATH.' }
}
elseif ($claudeCli) {
    try {
        $ya = & claude mcp list 2>&1 | Out-String
        if ($ya -match [regex]::Escape($NombreServidor)) {
            Write-Ok "Claude Code: '$NombreServidor' ya estaba registrado."
        } else {
            & claude mcp add $NombreServidor --scope user -- cmd /c npx -y $PaqueteNpm 2>&1 | Out-Null
            Write-Ok "Claude Code: servidor '$NombreServidor' registrado (scope user)."
        }
    } catch {
        Write-Aviso "Fallo 'claude mcp add' -> $($_.Exception.Message). Se editara el archivo de config."
        $claudeCli = $null
    }
}

$cfgCode = Join-Path $env:USERPROFILE '.claude.json'

if (-not $SoloVerificar -and -not $claudeCli -and -not (Test-Path $cfgCode)) {
    # el alumno no usa Claude Code: no tiene sentido crearle el archivo
    Write-Paso 'Claude Code no esta instalado en este equipo. Se omite (se usara Claude Desktop).'
}
elseif (-not $SoloVerificar -and -not $claudeCli) {
    try {
        Copy-Item $cfgCode "$cfgCode.bak-revitmcp" -Force
        $j = Get-Content $cfgCode -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $j.PSObject.Properties['mcpServers']) {
            $j | Add-Member -MemberType NoteProperty -Name mcpServers -Value (New-Object PSObject)
        }
        $srv = New-Object PSObject
        $srv | Add-Member -MemberType NoteProperty -Name type    -Value 'stdio'
        $srv | Add-Member -MemberType NoteProperty -Name command -Value $comando
        $srv | Add-Member -MemberType NoteProperty -Name args    -Value $argsMcp
        $j.mcpServers | Add-Member -MemberType NoteProperty -Name $NombreServidor -Value $srv -Force
        ($j | ConvertTo-Json -Depth 100) | Set-Content $cfgCode -Encoding UTF8
        Write-Ok "Claude Code: escrito en $cfgCode (respaldo: .claude.json.bak-revitmcp)"
    } catch {
        Write-Falla "No se pudo escribir la config de Claude Code -> $($_.Exception.Message)"
    }
}

# ---- 4b. Claude Desktop
$cfgDesktop = Join-Path $env:APPDATA 'Claude\claude_desktop_config.json'
$hayDesktop = Test-Path (Join-Path $env:APPDATA 'Claude')

if (-not $hayDesktop) {
    Write-Aviso 'Claude Desktop no parece instalado (no existe %AppData%\Claude). Se omite.'
}
elseif ($SoloVerificar) {
    if (Test-Path $cfgDesktop) {
        $txt = Get-Content $cfgDesktop -Raw -Encoding UTF8
        if ($txt -match [regex]::Escape($PaqueteNpm)) {
            Write-Ok 'Claude Desktop: servidor de Revit ya configurado.'
        } else {
            Write-Aviso 'Claude Desktop: existe la config pero sin el servidor de Revit.'
        }
    } else {
        Write-Aviso 'Claude Desktop: aun no existe claude_desktop_config.json.'
    }
}
else {
    try {
        if (Test-Path $cfgDesktop) {
            Copy-Item $cfgDesktop "$cfgDesktop.bak-revitmcp" -Force
            $d = Get-Content $cfgDesktop -Raw -Encoding UTF8 | ConvertFrom-Json
        } else {
            New-Item -ItemType Directory -Path (Split-Path $cfgDesktop) -Force | Out-Null
            $d = New-Object PSObject
        }
        if (-not $d.PSObject.Properties['mcpServers']) {
            $d | Add-Member -MemberType NoteProperty -Name mcpServers -Value (New-Object PSObject)
        }
        $srvD = New-Object PSObject
        $srvD | Add-Member -MemberType NoteProperty -Name command -Value $comando
        $srvD | Add-Member -MemberType NoteProperty -Name args    -Value $argsMcp
        $d.mcpServers | Add-Member -MemberType NoteProperty -Name $NombreServidor -Value $srvD -Force
        ($d | ConvertTo-Json -Depth 100) | Set-Content $cfgDesktop -Encoding UTF8
        Write-Ok "Claude Desktop: escrito en $cfgDesktop"
    } catch {
        Write-Falla "No se pudo escribir la config de Claude Desktop -> $($_.Exception.Message)"
    }
}

# ---------------------------------------------------------------- 5. prueba
Write-Titulo '5. Precarga del servidor MCP'

if ($SoloVerificar -or (Get-NodeMajor) -lt 18) {
    Write-Paso 'Se omite (modo diagnostico o Node no disponible).'
} else {
    try {
        Write-Paso "Descargando el paquete npm '$PaqueteNpm' a la cache de npx ..."
        & cmd /c "npx -y $PaqueteNpm --help" 2>&1 | Out-Null
        Write-Ok 'Paquete npm en cache: el primer arranque dentro de Claude sera rapido.'
    } catch {
        Write-Aviso 'No se pudo precargar el paquete npm; Claude lo bajara en el primer uso.'
    }
}

# ---------------------------------------------------------------- resumen
Write-Titulo 'Resumen'

if ($script:Errores.Count -eq 0 -and $SoloVerificar) {
    Write-Host '   Diagnostico terminado (no se modifico nada).' -ForegroundColor Green
} elseif ($script:Errores.Count -eq 0) {
    Write-Host '   Instalacion completada.' -ForegroundColor Green
} else {
    Write-Host "   Termino con $($script:Errores.Count) error(es):" -ForegroundColor Red
    foreach ($e in $script:Errores) { Write-Host "     - $e" -ForegroundColor Red }
}
if ($script:Advertencias.Count -gt 0) {
    Write-Host "   Advertencias ($($script:Advertencias.Count)):" -ForegroundColor Yellow
    foreach ($a in $script:Advertencias) { Write-Host "     - $a" -ForegroundColor Yellow }
}

Write-Host ''
if ($SoloVerificar) {
    Write-Host '   Para instalar de verdad, vuelve a ejecutar sin -SoloVerificar.' -ForegroundColor White
    Write-Host ''
    exit 0
}
Write-Host '   PASOS MANUALES QUE FALTAN:' -ForegroundColor White
Write-Host '     1. Reinicia Claude Desktop / Claude Code para que lea la nueva configuracion.'
Write-Host '     2. Abre Revit. Si pregunta por un complemento desconocido, elige SIEMPRE CARGAR.'
Write-Host '     3. En la cinta de Revit busca la pestana del add-in MCP y entra en Settings.'
Write-Host '     4. Activa los comandos que quieras habilitar y pulsa Save.'
Write-Host '     5. Abre un proyecto y preguntale a Claude: cuantos muros hay en mi modelo Revit'
Write-Host ''

if ($script:Errores.Count -gt 0) { exit 1 }
