---
name: revit-bim-assistant
description: Usa esta skill siempre que el usuario pregunte por elementos, parametros, niveles, ejes, habitaciones, muros, suelos, familias o geometria dentro de su modelo Revit. Se activa con frases como "en mi modelo Revit", "lista los elementos", "cuantos muros hay", "vista actual", "Revit", "modelo BIM", "muros", "puertas", "ventanas", "niveles", "ejes", "cuartos", "habitaciones", "tabla de planificacion", "etiquetar habitaciones", "exportar datos de cuartos", "cantidades de material", "crear muro", "crear nivel", "crear eje", "crear habitacion", "modificar elemento", "seleccionar elementos". Usala cuando el usuario espere que Claude lea o escriba en un proyecto de Revit abierto a traves de las tools revit-mcp.
---

# Revit BIM Assistant

Asistente para trabajar con modelos Revit a traves del servidor MCP `revit-mcp` que corre localmente en la maquina del usuario.

## Prerrequisitos antes de llamar cualquier tool

1. Revit (2020-2026) abierto con un proyecto cargado.
2. El add-in de MCP instalado en `%AppData%\Autodesk\Revit\Addins\<anio>\`.
3. Dentro de Revit, los comandos activados en el panel **Settings** del add-in (y guardados con **Save**).

Si una tool falla con timeout o "connection refused", el problema casi siempre es uno de esos tres puntos. Verifica en ese orden y, si hay que reinstalar o diagnosticar a fondo, cambia a la skill `instalar-revit-mcp`.

## Tools disponibles

Se invocan como `mcp__revit-mcp__<nombre>`.

### Lectura / consulta
- `say_hello` — ping de salud de la conexion
- `get_current_view_info` — info de la vista activa
- `get_current_view_elements` — elementos visibles en la vista actual
- `get_selected_elements` — elementos seleccionados por el usuario
- `get_available_family_types` — familias y tipos cargados en el proyecto
- `analyze_model_statistics` — metricas globales del modelo
- `get_material_quantities` — cantidades de material
- `ai_element_filter` — filtro semantico de elementos por descripcion en lenguaje natural

### Creacion
- `create_level` — niveles
- `create_grid` — ejes
- `create_room` — habitaciones
- `create_point_based_element` — familias point-based (puertas, ventanas, mobiliario)
- `create_line_based_element` — familias line-based (muros, vigas, tuberias)
- `create_surface_based_element` — familias surface-based (suelos, techos, cubiertas)
- `create_structural_framing_system` — sistemas estructurales
- `create_dimensions` — cotas en la vista actual

### Modificacion
- `operate_element` — operaciones sobre elementos (seleccionar, ocultar, colorear, mover)
- `delete_element` — eliminar elementos por ID
- `color_elements` — colorear elementos segun el valor de un parametro
- `tag_all_walls` — etiquetar todos los muros de la vista
- `tag_all_rooms` — etiquetar todas las habitaciones de la vista

### Exportacion / datos
- `export_room_data` — exporta data de habitaciones (area, perimetro, nivel)
- `store_project_data` / `store_room_data` — guarda datos en la base local del servidor
- `query_stored_data` — consulta datos previamente guardados

### Avanzado
- `send_code_to_revit` — ejecuta codigo C# directamente en el contexto de Revit. Potente y peligroso: confirmar siempre con el usuario antes de usarlo.

## Patron de respuesta

1. Identifica que tool aplica. Ante la duda, prefiere lectura sobre escritura.
2. Llama la tool y procesa el resultado.
3. Resume en espanol claro, con numeros concretos. No pegues el JSON crudo salvo que lo pidan.
4. Si la tool requiere seleccion previa (`get_selected_elements`), pide primero que seleccione los elementos en Revit.

## Operaciones destructivas (delete, modificacion masiva, creacion masiva)

Antes de ejecutar:
- Repite que vas a hacer y a cuantos elementos afecta.
- Espera confirmacion explicita.
- Sugiere guardar el proyecto en Revit antes.

## Casos comunes

| Pregunta del usuario | Tool a llamar |
|---|---|
| "Que hay en la vista actual?" | `get_current_view_elements` |
| "Cuantos muros tengo?" | `analyze_model_statistics` |
| "Lista los tipos de puerta cargados" | `get_available_family_types` |
| "Etiqueta todas las habitaciones" | `tag_all_rooms` |
| "Exporta las areas de los cuartos" | `export_room_data` |
| "Crea un nivel a +3.50 m llamado N2" | `create_level` |
| "Cuanto hormigon hay en el modelo?" | `get_material_quantities` |
| "Pinta de rojo los muros tipo X" | `color_elements` |
| "Se cayo la conexion / da timeout" | cambiar a la skill `instalar-revit-mcp` |
