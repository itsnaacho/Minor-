# Guía Rápida — Taller 2 Power BI (Tareas 3–6)

## Paso 1: Preparar los datos (5 min)

1. Pon todos los CSV del Censo (`personas_valpo.csv`, `hogares_valpo.csv`, `vivienda_valpo.csv`) en la **misma carpeta** que `preparar_datos_powerbi.py`
2. Abre una terminal (cmd/PowerShell) en esa carpeta y ejecuta:
   ```
   python preparar_datos_powerbi.py
   ```
3. Se generarán estos archivos listos para Power BI:

| Archivo | Uso |
|---|---|
| `tarea3_hacinamiento.csv` | Tabla resumen por comuna (hacinamiento) |
| `tarea3_hacinamiento_detalle.csv` | Detalle hogar por hogar (scatter plot) |
| `tarea4_educacion_actividad.csv` | Cruce educación × condición laboral |
| `tarea4_educacion_actividad_pct.csv` | Porcentajes por comuna |
| `tarea5_servicios_basicos.csv` | Acceso agua/electricidad/alcantarillado |
| `tarea6_indicador_desarrollo.csv` | Indicador compuesto + prioridad política pública |

> **Si el script dice "AVISO: columna no encontrada"**, revisa qué nombres tienen las columnas en tus CSV (el script los imprime al inicio) y ajusta las variables en la sección "Configuración" al inicio del script.

---

## Paso 2: Importar en Power BI

Inicio → Obtener datos → Texto/CSV → selecciona cada archivo → Cargar

Importa los 6 archivos. Luego en "Modelo" conecta por la columna `comuna` / `nombre_comuna`.

---

## Paso 3: Visualizaciones por tarea

### Tarea 3 — Hacinamiento y Tamaño del Hogar

**Tabla `tarea3_hacinamiento.csv`**

| Visualización | Campos |
|---|---|
| **Mapa de burbujas** | Ubicación: `comuna` · Tamaño: `pct_hacinados` · Color: `indice_hacinamiento_promedio` |
| **Gráfico de barras** | Eje X: `comuna` · Valor: `pct_hacinados` · Ordenar desc. |
| **Treemap** | Grupo: `provincia` → `comuna` · Valor: `pct_hacinados` |
| **Tarjeta KPI** | `pct_hacinados` máximo (comuna más crítica) |

**Tabla `tarea3_hacinamiento_detalle.csv`**

| Visualización | Campos |
|---|---|
| **Scatter plot** | Eje X: `n_personas` · Eje Y: `n_cuartos` · Tamaño/Color: `indice_hacinamiento` · Leyenda: `categoria_hacinamiento` |

**Slicer:** `categoria_hacinamiento` (Sin hacinamiento / Medio / Alto / Crítico)

---

### Tarea 4 — Nivel Educativo y Condición de Actividad

**Tabla `tarea4_educacion_actividad.csv`**

| Visualización | Campos |
|---|---|
| **Gráfico de barras apiladas** | Eje X: `nivel_educativo_label` · Valor: `n_personas` · Leyenda: `condicion_actividad_label` |
| **Tabla dinámica / Matrix** | Filas: `nivel_educativo_label` · Columnas: `condicion_actividad_label` · Valor: `n_personas` |
| **Heatmap** (Matrix con formato condicional) | Filas: `nivel_educativo_label` · Columnas: `condicion_actividad_label` · Valor: suma · Formato condicional por fondo |

**Tabla `tarea4_educacion_actividad_pct.csv`**

| Visualización | Campos |
|---|---|
| **Gráfico de barras 100% apiladas** | Eje X: `nivel_educativo_label` · Valor: `porcentaje` · Leyenda: `condicion_actividad_label` |

**Slicers:** `nombre_provincia`, `nombre_comuna`

---

### Tarea 5 — Acceso a Servicios Básicos

**Tabla `tarea5_servicios_basicos.csv`**

| Visualización | Campos |
|---|---|
| **Gráfico de barras agrupadas** | Eje X: `comuna` · Valores: `pct_agua`, `pct_electricidad`, `pct_alcantarillado` |
| **Heatmap** (Matrix + formato condicional) | Filas: `comuna` · Columnas: los 3 servicios · Escala roja (peor) a verde (mejor) |
| **Mapa de burbujas** | Ubicación: `comuna` · Tamaño: `indice_brecha_servicios` |
| **Tarjetas KPI** | `pct_agua` promedio, `pct_electricidad` promedio, `pct_alcantarillado` promedio |
| **Gráfico de barras** | Eje X: `comuna` · Valor: `indice_brecha_servicios` · Ordenar desc → "comunas con mayor brecha" |

**Slicer:** `nombre_provincia`

---

### Tarea 6 — Indicador de Desarrollo y Política Pública

**Tabla `tarea6_indicador_desarrollo.csv`**

| Visualización | Campos |
|---|---|
| **Mapa de burbujas** | Ubicación: `comuna` · Tamaño: `indicador_desarrollo_compuesto` · Color: `prioridad_politica_publica` |
| **Treemap** | Grupo: `prioridad_politica_publica` → `comuna` · Valor: `indicador_desarrollo_compuesto` |
| **Gráfico de barras** | Eje X: `comuna` · Valor: `indicador_desarrollo_compuesto` · Color: `prioridad_politica_publica` · Ordenar desc |
| **Scatter plot** | Eje X: `pct_hacinamiento_norm` · Eje Y: `pct_educ_baja_norm` · Tamaño: `pct_mayores65_norm` · Leyenda: `prioridad_politica_publica` |
| **Tabla** | `comuna`, `provincia`, todos los `_norm`, `indicador_desarrollo_compuesto`, `prioridad_politica_publica` |

**Slicer:** `prioridad_politica_publica` (Alta / Media / Baja)

---

## Estructura del Indicador Compuesto (Tarea 6)

El indicador combina 4 dimensiones, cada una normalizada 0–100 (donde 100 = peor situación):

```
Indicador = promedio(
  pct_mayores65_norm,        ← envejecimiento
  pct_educ_baja_norm,        ← bajo nivel educativo
  pct_hacinamiento_norm,     ← hacinamiento
  pct_brecha_servicios_norm  ← falta de servicios básicos
)
```

- **Alta prioridad** = tercio superior del indicador → comunas más vulnerables
- **Media prioridad** = tercio medio
- **Baja prioridad** = tercio inferior

---

## Tips para Power BI

- **Mapa de burbujas**: necesitas el visual "Azure Maps" o "ArcGIS Maps". Si no lo tienes, usa "Mapa" nativo con la columna `comuna` (Power BI lo geocodifica automáticamente).
- **Heatmap**: usa el visual "Matrix" con formato condicional de fondo → Escala de colores.
- **Drill-down en treemap**: arrastra `provincia` como primer nivel y `comuna` como segundo en el campo "Grupo".
- **Formato condicional en barras**: selecciona la barra → Formato → Color de datos → fx → basado en `prioridad_politica_publica`.
- **Slicers en cascada**: conecta el slicer de provincia al de comuna usando la relación en el modelo.
