---
name: instalar-revit-mcp
description: Instala, repara y diagnostica la conexion entre Claude y Autodesk Revit (servidor MCP revit-mcp). Usa esta skill cuando el usuario diga "instalar revit mcp", "conectar Claude con Revit", "configurar el MCP de Revit", "no me funcionan las herramientas de Revit", "las tools dan timeout", "no aparece revit-mcp", "instalar el plugin de Revit", "setup del curso MCP", "dejar todo listo para el curso", o cuando cualquier tool mcp__revit-mcp__* falle por conexion. Tambien cuando pregunte que le falta instalar para trabajar con Revit desde Claude.
---

# Instalar y diagnosticar revit-mcp

Objetivo: dejar funcionando la cadena completa y, si ya esta, decir en que eslabon se rompio.

```
Claude  <--stdio-->  mcp-server-for-revit (Node)  <--WebSocket-->  Add-in de Revit  -->  Revit API
```

Los cuatro eslabones, en el orden en que hay que verificarlos:

| # | Eslabon | Como se comprueba |
|---|---------|-------------------|
| 1 | Node.js 18+ | `node -v` |
| 2 | Add-in en Revit | existe un `*.addin` con "mcp" en `%AppData%\Autodesk\Revit\Addins\<anio>\` |
| 3 | Servidor MCP registrado en Claude | aparecen tools `mcp__revit-mcp__*` |
| 4 | Servicio arrancado dentro de Revit | Revit abierto, con proyecto, y comandos activados en el panel Settings del add-in |

## Flujo cuando el usuario pide instalar

1. Ejecuta el diagnostico primero. Nunca instales a ciegas. Si el repo esta clonado en el disco:

   ```powershell
   .\install.ps1 -SoloVerificar
   ```

   Si no esta clonado, descarga el script a una carpeta temporal y diagnostica desde ahi:

   ```powershell
   $s = "$env:TEMP\install-revit-mcp.ps1"
   irm https://raw.githubusercontent.com/thebimcowork-lab/THEBIMCOWORK/main/install.ps1 -OutFile $s
   & $s -SoloVerificar
   ```

2. Lee el resumen del diagnostico y explica en espanol claro que falta. No pegues la salida cruda entera.

3. Ejecuta el instalador real solo despues de confirmarlo con el usuario, y avisando que **Revit debe estar cerrado**. Usa el mismo `install.ps1` del paso 1, sin `-SoloVerificar`:

   ```powershell
   & $s
   ```

   Variantes utiles:
   - `-RevitVersions 2024,2025` cuando Revit no esta en la ruta estandar o solo se quiere una version.
   - `-OmitirNode` en equipos corporativos sin permisos para instalar Node.

4. Al terminar, recuerda siempre los pasos que el script NO puede hacer por si mismo:
   - Reiniciar Claude Desktop / Claude Code.
   - Abrir Revit y elegir **Siempre cargar** si aparece el aviso de complemento desconocido.
   - Entrar a **Settings** en la pestana del add-in dentro de Revit, activar los comandos y pulsar **Save**.

5. Verifica de punta a punta llamando `mcp__revit-mcp__say_hello`. Si responde, la cadena esta viva.

## Flujo cuando algo falla

Diagnostica de abajo hacia arriba, que es el orden en que se rompe en la practica:

| Sintoma | Causa mas probable | Que hacer |
|---|---|---|
| No existe ninguna tool `mcp__revit-mcp__*` | el servidor no esta registrado, o Claude no se reinicio | correr el instalador y reiniciar Claude |
| Las tools existen pero dan **timeout** o "connection refused" | Revit cerrado, sin proyecto, o comandos sin activar en Settings | pedir al usuario que abra Revit con un modelo y revise Settings > Save |
| Error `cannot find module` | falta la instalacion local en `%LocalAppData%\revit-mcp-server\` o Node cambio de ruta | volver a correr el instalador |
| npm intenta compilar better-sqlite3 y falla pidiendo Visual Studio | se instalo el paquete sin el override (npx directo con Node 24) | usar SIEMPRE el instalador, que fija better-sqlite3 12.x con binarios |
| Revit no muestra la pestana del add-in | el `.addin` quedo en la carpeta de otra version de Revit | verificar `%AppData%\Autodesk\Revit\Addins\<anio>\` para el anio correcto |
| El add-in aparece pero Revit lo bloquea | Revit estaba abierto durante la copia, o el complemento quedo sin autorizar | cerrar Revit, reinstalar, y elegir **Siempre cargar** al abrir |
| Una tool concreta falla y el resto funciona | ese comando no esta habilitado en Settings | activarlo en el panel Settings del add-in |

Comprobaciones sueltas que puedes lanzar tu mismo:

```powershell
node -v
Get-ChildItem "$env:APPDATA\Autodesk\Revit\Addins" -Recurse -Filter *.addin | Select-Object FullName
Get-Process Revit -ErrorAction SilentlyContinue | Select-Object Id, MainWindowTitle
```

## Reglas

- El add-in solo soporta **Revit 2020 a 2026**. Fuera de ese rango, dilo y no intentes instalar.
- Nunca copies archivos al directorio de add-ins con Revit abierto: los DLL quedan bloqueados y la instalacion queda a medias.
- El instalador respalda las configuraciones que toca (`.bak-revitmcp`). Si algo queda mal, se restauran esos archivos.
- No inventes rutas ni versiones: si el diagnostico no las reporta, preguntale al usuario.
- Una vez instalado, el trabajo con el modelo se hace con la skill `revit-bim-assistant`.
