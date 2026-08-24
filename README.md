# Instalador revit-mcp · Curso MCP + Claude

Instalador de un solo paso para conectar **Claude** con **Autodesk Revit**.
Al terminar, podrás preguntarle a Claude cosas como *"¿cuántos muros hay en mi modelo?"* y que las responda leyendo tu proyecto abierto.

**The BIM Co-Work · Método TBC**

---

## Qué se instala

```
Claude  ──stdio──►  Servidor MCP (Node)  ──WebSocket──►  Add-in de Revit  ──►  Revit API
```

| Componente | Qué es | Dónde queda |
|---|---|---|
| Add-in de Revit | Plugin C# que ejecuta las órdenes dentro de Revit | `%AppData%\Autodesk\Revit\Addins\<año>\` |
| Node.js 18+ | Motor del servidor MCP | instalado por winget si falta |
| Servidor MCP | `mcp-server-for-revit` (instalación npm local) | `%LocalAppData%\revit-mcp-server\` |
| Registro en Claude | Claude Code y/o Claude Desktop | `.claude.json` / `claude_desktop_config.json` |

---

## Requisitos

- Windows 10/11
- Autodesk Revit **2020 – 2026** instalado
- Claude Desktop o Claude Code
- Conexión a internet (descarga ~10–20 MB)

No hace falta ser administrador salvo que haya que instalar Node.js.

---

## Instalación

### Opción A — un solo comando (recomendada)

Abre **PowerShell** y pega:

```powershell
irm https://raw.githubusercontent.com/thebimcowork-lab/THEBIMCOWORK/main/install.ps1 | iex
```

### Opción B — clonando el repo

```powershell
git clone https://github.com/thebimcowork-lab/THEBIMCOWORK.git
cd THEBIMCOWORK
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

> **Cierra Revit antes de ejecutar.** Si está abierto, los archivos del add-in quedan bloqueados y la instalación queda a medias.

### Ver qué falta sin instalar nada

```powershell
.\install.ps1 -SoloVerificar
```

### Otras variantes

```powershell
.\install.ps1 -RevitVersions 2024,2025   # solo estas versiones
.\install.ps1 -OmitirNode                # no instalar Node (equipos corporativos)
```

---

## Después de instalar (esto es manual, el script no puede hacerlo)

1. **Reinicia** Claude Desktop / Claude Code.
2. Abre **Revit**. Si aparece el aviso de complemento desconocido, elige **Siempre cargar**.
3. En la cinta de Revit, entra en la pestaña del add-in MCP → **Settings** → activa los comandos → **Save**.
4. Abre un proyecto y prueba en Claude:
   > ¿Cuántos muros hay en mi modelo Revit?

---

## Skills de Claude (opcional pero recomendado)

Este repo también es un *marketplace* de plugins de Claude Code. Instálalo para que Claude sepa usar Revit y sepa repararse solo:

```
/plugin marketplace add thebimcowork-lab/THEBIMCOWORK
/plugin install revit-mcp-cowork@thebimcowork
```

Trae dos skills:

- **`revit-bim-assistant`** — mapa de las 25+ herramientas y cómo usarlas con criterio BIM.
- **`instalar-revit-mcp`** — diagnostica y repara la conexión cuando algo falla. Basta con decirle a Claude *"no me funcionan las tools de Revit"*.

---

## Si algo no funciona

| Síntoma | Causa probable | Solución |
|---|---|---|
| No aparecen las herramientas de Revit | Claude no se reinició | Cierra y abre Claude por completo |
| Timeout / "connection refused" | Revit cerrado, sin proyecto, o comandos sin activar | Abre Revit con un modelo y revisa **Settings → Save** |
| `cannot find module` | Servidor local borrado o Node reinstalado en otra ruta | Vuelve a correr el instalador |
| No hay pestaña del add-in en Revit | El `.addin` quedó en la carpeta de otro año | Revisa `%AppData%\Autodesk\Revit\Addins\<año>\` |
| Revit bloquea el complemento | Estaba abierto al instalar | Ciérralo, reinstala y elige **Siempre cargar** |

Diagnóstico completo en cualquier momento:

```powershell
.\install.ps1 -SoloVerificar
```

El instalador respalda todo lo que toca con la extensión `.bak-revitmcp`.

---

## Créditos

El servidor MCP y el add-in son el proyecto comunitario de código abierto
[mcp-servers-for-revit](https://github.com/mcp-servers-for-revit/mcp-servers-for-revit),
fork del original [revit-mcp](https://github.com/mcp-servers-for-revit/revit-mcp).

Este repositorio solo automatiza su instalación y configuración para los alumnos del curso.
