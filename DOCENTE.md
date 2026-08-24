# Guía del docente — puesta en marcha del repo

Notas internas para Rafael. **No es material del alumno.**

---

## 1. Publicar el repo

```bash
cd "C:\Users\THE BIM CO-WORK\Desktop\revit-mcp-setup"
git init
git add .
git commit -m "Instalador revit-mcp para el curso MCP + Claude"
gh repo create thebimcowork-lab/THEBIMCOWORK --public --source=. --push
```

El repo **debe ser público** y la rama **debe llamarse `main`**: el comando de una línea que usan los alumnos apunta a `raw.githubusercontent.com/thebimcowork-lab/THEBIMCOWORK/main/install.ps1`.

Si cambias de cuenta o de nombre, hay que reemplazar `thebimcowork-lab/THEBIMCOWORK` en tres sitios:
`README.md`, `plugins/revit-mcp-cowork/.claude-plugin/plugin.json` y
`plugins/revit-mcp-cowork/skills/instalar-revit-mcp/SKILL.md`.

---

## 2. Verificación previa a clase (hazla una vez en un equipo limpio)

```powershell
.\install.ps1 -SoloVerificar   # debe listar 4 advertencias en una máquina virgen
.\install.ps1                  # instalación real, con Revit cerrado
```

Luego, dentro de Claude, `mcp__revit-mcp__say_hello` debe responder con Revit abierto.

---

## 3. Qué versión queda instalada

El script pregunta a la API de GitHub por el **último release** de
`mcp-servers-for-revit/mcp-servers-for-revit` y descarga el ZIP del año de Revit detectado.
Si GitHub no responde, cae a la constante `$TagPorDefecto` (hoy `v1.0.0`).

Cuando salga una versión nueva del add-in, actualiza esa constante en `install.ps1`
para que el *fallback* no quede viejo.

---

## 4. Trampas conocidas en sala

| Problema en clase | Prevención |
|---|---|
| Alumnos con Revit abierto | Dilo antes de dar el comando: **cerrar Revit primero** |
| Equipos sin Node y sin permisos de admin | `-OmitirNode`, e instalar Node antes por IT |
| `ExecutionPolicy` bloquea el `.ps1` | El one-liner `irm ... \| iex` la evita; el `.ps1` local necesita `-ExecutionPolicy Bypass` |
| Revit instalado fuera de `C:\Program Files\Autodesk` | `-RevitVersions 2024` a mano |
| Antivirus corporativo bloquea la descarga del ZIP | Ten los ZIP en un pendrive como plan B |
| Se olvidan de **Settings → Save** en Revit | Es el fallo #1: las tools existen pero dan timeout |

---

## 5. Diferencia con la instalación vieja de este equipo

El plugin `revit-mcp-cowork` que ya tenías apuntaba a una ruta absoluta de otra máquina:

```
C:\Users\arqra\AppData\Roaming\npm\node_modules\mcp-server-for-revit\build\index.js
```

Eso no es portable. La versión de este repo usa `cmd /c npx -y mcp-server-for-revit`,
que funciona en cualquier equipo sin instalación global de npm.

Nota: en este equipo (`THE BIM CO-WORK`) el add-in **no** está instalado y **no** hay Node.
Solo hay Revit 2023. Si vas a demostrar en vivo desde aquí, corre el instalador antes.
