# -*- coding: utf-8 -*-
"""
Taller 2 - Preparación de datos para Power BI
Tareas 3 a 6 - Censo 2024 Región de Valparaíso

Ejecutar este script con los archivos CSV en la misma carpeta.
Genera CSVs listos para importar directamente en Power BI.

Uso:
    python preparar_datos_powerbi.py

Archivos de entrada requeridos:
    - personas_valpo.csv  (o personas_valpo1.csv)
    - hogares_valpo.csv   (o hogares_valpo1.csv)
    - vivienda_valpo.csv  (o vivienda_valpo1.csv)

Archivos de salida generados:
    - tarea3_hacinamiento.csv
    - tarea4_educacion_actividad.csv
    - tarea5_servicios_basicos.csv
    - tarea6_indicador_desarrollo.csv
"""

import pandas as pd
import numpy as np
import os
import sys

# ── Configuración: ajusta estos nombres si tu archivo tiene nombres distintos ──
PERSONAS_FILE  = 'personas_valpo.csv'
HOGARES_FILE   = 'hogares_valpo.csv'
VIVIENDA_FILE  = 'vivienda_valpo.csv'

# Nombres de columnas clave (INE Censo 2024)
# Si tu CSV usa nombres distintos, cámbialos aquí
COL_COMUNA     = 'nombre_comuna'   # Nombre de la comuna
COL_PROVINCIA  = 'nombre_provincia'
COL_REGION     = 'region'

# Personas
COL_EDAD       = 'p09'   # Edad en años
COL_SEXO       = 'p08'   # 1=Hombre, 2=Mujer
COL_EDUC       = 'p14'   # Nivel educativo máximo alcanzado
COL_ACTIVIDAD  = 'p18'   # Condición de actividad (1=Ocupado, 2=Desocupado, 3=Inactivo)

# Hogares
COL_N_PERSONAS = 'cant_per'    # Número de personas en el hogar
COL_N_CUARTOS  = 'cant_cuar'   # Número de cuartos/dormitorios exclusivos

# Vivienda (acceso a servicios - típicamente: 1=Sí accede, valores >1 = sin acceso o alternativa)
COL_AGUA       = 'p03'   # Acceso a agua potable (procedencia del agua)
COL_ELECTRIC   = 'p04'   # Acceso a electricidad
COL_ALCANT     = 'p05'   # Sistema de eliminación de aguas servidas

# ──────────────────────────────────────────────────────────────────────────────


def cargar_csv(filename, alternativo=None):
    """Carga un CSV, intenta el archivo alternativo si el principal no existe."""
    for f in [filename, alternativo]:
        if f and os.path.exists(f):
            print(f"  Cargando: {f} ...")
            df = pd.read_csv(f, sep=None, engine='python', encoding='utf-8', low_memory=False)
            print(f"  -> {len(df):,} filas, {len(df.columns)} columnas")
            return df
    print(f"  ERROR: No se encontró {filename}. Verifica que el archivo esté en la misma carpeta.")
    return None


def detectar_columna(df, candidatos, nombre_logico):
    """Busca entre candidatos cuál columna existe en el dataframe."""
    for c in candidatos:
        if c in df.columns:
            return c
    # Intenta búsqueda parcial (insensible a mayúsculas)
    for c in df.columns:
        for cand in candidatos:
            if cand.lower() in c.lower():
                print(f"  [AVISO] Usando '{c}' para '{nombre_logico}' (coincidencia parcial)")
                return c
    print(f"  [AVISO] No se encontró columna para '{nombre_logico}'. Candidatos: {candidatos}")
    print(f"  Columnas disponibles: {list(df.columns)}")
    return None


def normalizar_columnas(df):
    """Convierte nombres de columnas a minúsculas y sin espacios extra."""
    df.columns = df.columns.str.strip().str.lower()
    return df


# ══════════════════════════════════════════════════════════════════════════════
# TAREA 3 — Hacinamiento y Tamaño del Hogar
# ══════════════════════════════════════════════════════════════════════════════
def tarea3_hacinamiento(df_hog):
    print("\n=== TAREA 3: Hacinamiento y Tamaño del Hogar ===")

    # Detectar columnas
    col_com  = detectar_columna(df_hog, [COL_COMUNA, 'comuna', 'nom_comuna', 'nombre_comuna'], 'comuna')
    col_prov = detectar_columna(df_hog, [COL_PROVINCIA, 'provincia', 'nom_provincia'], 'provincia')
    col_per  = detectar_columna(df_hog, [COL_N_PERSONAS, 'n_personas', 'tot_per', 'personas_hogar', 'p_personas'], 'n_personas_hogar')
    col_cuar = detectar_columna(df_hog, [COL_N_CUARTOS, 'n_cuartos', 'cant_cuartos', 'cuartos', 'p_cuartos', 'n_dormitorios'], 'n_cuartos')

    if not all([col_com, col_per, col_cuar]):
        print("  No se pudo procesar Tarea 3 por columnas faltantes.")
        return

    df = df_hog.copy()

    # Filtrar datos válidos (al menos 1 cuarto para evitar división por 0)
    df = df[df[col_cuar].notna() & (df[col_cuar] > 0)]
    df = df[df[col_per].notna() & (df[col_per] > 0)]

    # Calcular índice de hacinamiento: personas / cuartos
    df['indice_hacinamiento'] = df[col_per] / df[col_cuar]

    # Clasificar hacinamiento según estándar MINVU:
    # <= 2.4 = Sin hacinamiento
    # 2.5 - 3.4 = Hacinamiento medio
    # 3.5 - 4.9 = Hacinamiento alto
    # >= 5.0 = Hacinamiento crítico
    def clasificar(idx):
        if idx <= 2.4:
            return 'Sin hacinamiento'
        elif idx <= 3.4:
            return 'Hacinamiento medio'
        elif idx <= 4.9:
            return 'Hacinamiento alto'
        else:
            return 'Hacinamiento crítico'

    df['categoria_hacinamiento'] = df['indice_hacinamiento'].apply(clasificar)

    group_cols = [c for c in [col_prov, col_com] if c]

    # Agregación por comuna
    resultado = df.groupby(group_cols).agg(
        total_hogares=(col_per, 'count'),
        promedio_personas_hogar=(col_per, 'mean'),
        promedio_cuartos=(col_cuar, 'mean'),
        indice_hacinamiento_promedio=('indice_hacinamiento', 'mean'),
        hogares_sin_hacinamiento=('categoria_hacinamiento', lambda x: (x == 'Sin hacinamiento').sum()),
        hogares_hacinamiento_medio=('categoria_hacinamiento', lambda x: (x == 'Hacinamiento medio').sum()),
        hogares_hacinamiento_alto=('categoria_hacinamiento', lambda x: (x == 'Hacinamiento alto').sum()),
        hogares_hacinamiento_critico=('categoria_hacinamiento', lambda x: (x == 'Hacinamiento crítico').sum()),
    ).reset_index()

    resultado['pct_hacinados'] = (
        (resultado['hogares_hacinamiento_medio'] +
         resultado['hogares_hacinamiento_alto'] +
         resultado['hogares_hacinamiento_critico']) / resultado['total_hogares'] * 100
    ).round(2)

    resultado = resultado.round(3)
    resultado.to_csv('tarea3_hacinamiento.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ Exportado: tarea3_hacinamiento.csv ({len(resultado)} comunas)")

    # Tabla detallada por hogar (para scatter plot en PBI)
    detalle = df[group_cols + [col_per, col_cuar, 'indice_hacinamiento', 'categoria_hacinamiento']].copy()
    detalle.columns = group_cols + ['n_personas', 'n_cuartos', 'indice_hacinamiento', 'categoria_hacinamiento']
    detalle.to_csv('tarea3_hacinamiento_detalle.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ Exportado: tarea3_hacinamiento_detalle.csv ({len(detalle):,} hogares)")


# ══════════════════════════════════════════════════════════════════════════════
# TAREA 4 — Nivel Educativo y Condición de Actividad
# ══════════════════════════════════════════════════════════════════════════════
def tarea4_educacion_actividad(df_per):
    print("\n=== TAREA 4: Educación y Condición de Actividad ===")

    col_com  = detectar_columna(df_per, [COL_COMUNA, 'comuna', 'nom_comuna', 'nombre_comuna'], 'comuna')
    col_prov = detectar_columna(df_per, [COL_PROVINCIA, 'provincia', 'nom_provincia'], 'provincia')
    col_educ = detectar_columna(df_per, [COL_EDUC, 'p14', 'nivel_educ', 'niv_educ', 'educacion'], 'nivel_educativo')
    col_act  = detectar_columna(df_per, [COL_ACTIVIDAD, 'p18', 'cond_actividad', 'condicion_actividad', 'condicion_ocup', 'p17'], 'condicion_actividad')
    col_edad = detectar_columna(df_per, [COL_EDAD, 'p09', 'edad'], 'edad')

    if not all([col_com, col_educ, col_act]):
        print("  No se pudo procesar Tarea 4 por columnas faltantes.")
        return

    df = df_per.copy()

    # Filtrar solo población en edad de trabajar (15+) para análisis de actividad
    if col_edad:
        df_activos = df[df[col_edad] >= 15].copy()
    else:
        df_activos = df.copy()

    # Mapear nivel educativo (códigos INE Censo 2024)
    mapa_educ = {
        0: '0. Sin educación formal',
        1: '1. Ed. Parvularia',
        2: '2. Básica incompleta',
        3: '3. Básica completa',
        4: '4. Media incompleta',
        5: '5. Media completa',
        6: '6. Técnica incompleta',
        7: '7. Técnica completa',
        8: '8. Universitaria incompleta',
        9: '9. Universitaria completa',
        10: '10. Postgrado',
        99: '99. Ignorado',
    }

    # Mapear condición de actividad (códigos INE Censo 2024)
    mapa_actividad = {
        1: 'Ocupado',
        2: 'Desocupado (busca trabajo)',
        3: 'Inactivo',
        9: 'No aplica / < 15 años',
    }

    df_activos['nivel_educativo_label'] = df_activos[col_educ].map(mapa_educ).fillna(df_activos[col_educ].astype(str))
    df_activos['condicion_actividad_label'] = df_activos[col_act].map(mapa_actividad).fillna(df_activos[col_act].astype(str))

    group_cols = [c for c in [col_prov, col_com] if c]

    # Tabla cruzada: educación × condición de actividad × comuna
    resultado = df_activos.groupby(
        group_cols + ['nivel_educativo_label', 'condicion_actividad_label']
    ).size().reset_index(name='n_personas')

    resultado.to_csv('tarea4_educacion_actividad.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ Exportado: tarea4_educacion_actividad.csv ({len(resultado):,} filas)")

    # Tabla resumen % por nivel educativo
    total_por_educ = df_activos.groupby(
        group_cols + ['nivel_educativo_label']
    ).size().reset_index(name='total_nivel')

    por_actividad = df_activos.groupby(
        group_cols + ['nivel_educativo_label', 'condicion_actividad_label']
    ).size().reset_index(name='n_personas')

    resumen = por_actividad.merge(total_por_educ, on=group_cols + ['nivel_educativo_label'])
    resumen['porcentaje'] = (resumen['n_personas'] / resumen['total_nivel'] * 100).round(2)

    resumen.to_csv('tarea4_educacion_actividad_pct.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ Exportado: tarea4_educacion_actividad_pct.csv")


# ══════════════════════════════════════════════════════════════════════════════
# TAREA 5 — Acceso a Servicios Básicos
# ══════════════════════════════════════════════════════════════════════════════
def tarea5_servicios_basicos(df_viv):
    print("\n=== TAREA 5: Acceso a Servicios Básicos ===")

    col_com  = detectar_columna(df_viv, [COL_COMUNA, 'comuna', 'nom_comuna', 'nombre_comuna'], 'comuna')
    col_prov = detectar_columna(df_viv, [COL_PROVINCIA, 'provincia', 'nom_provincia'], 'provincia')
    col_agua = detectar_columna(df_viv, [COL_AGUA, 'p03', 'agua', 'agua_potable', 'p3', 'proced_agua'], 'agua')
    col_elec = detectar_columna(df_viv, [COL_ELECTRIC, 'p04', 'electricidad', 'elec', 'p4'], 'electricidad')
    col_alc  = detectar_columna(df_viv, [COL_ALCANT, 'p05', 'alcantarillado', 'p5', 'sist_agua_serv'], 'alcantarillado')

    if not col_com:
        print("  No se pudo procesar Tarea 5 por columnas faltantes.")
        return

    df = df_viv.copy()
    group_cols = [c for c in [col_prov, col_com] if c]

    agg_dict = {'total_viviendas': (group_cols[0], 'count')}
    result_df = df.groupby(group_cols).size().reset_index(name='total_viviendas')

    # Agua potable: código 1 = Red pública (acceso formal) en Censo 2024
    # Cualquier otro código = sin acceso a red pública
    if col_agua:
        agua_agg = df.groupby(group_cols).apply(
            lambda x: (x[col_agua] == 1).sum()
        ).reset_index(name='con_agua_potable')
        result_df = result_df.merge(agua_agg, on=group_cols)

    # Electricidad: código 1 = Sí tiene
    if col_elec:
        elec_agg = df.groupby(group_cols).apply(
            lambda x: (x[col_elec] == 1).sum()
        ).reset_index(name='con_electricidad')
        result_df = result_df.merge(elec_agg, on=group_cols)

    # Alcantarillado: código 1 = Red pública de alcantarillado
    if col_alc:
        alc_agg = df.groupby(group_cols).apply(
            lambda x: (x[col_alc] == 1).sum()
        ).reset_index(name='con_alcantarillado')
        result_df = result_df.merge(alc_agg, on=group_cols)

    # Calcular porcentajes
    total = result_df['total_viviendas']
    for col_servicio, nombre in [
        ('con_agua_potable', 'agua'),
        ('con_electricidad', 'electricidad'),
        ('con_alcantarillado', 'alcantarillado'),
    ]:
        if col_servicio in result_df.columns:
            result_df[f'pct_{nombre}'] = (result_df[col_servicio] / total * 100).round(2)
            result_df[f'sin_{nombre}'] = total - result_df[col_servicio]
            result_df[f'pct_sin_{nombre}'] = (result_df[f'sin_{nombre}'] / total * 100).round(2)

    # Índice de brecha (promedio de los % sin acceso)
    pct_sin_cols = [c for c in result_df.columns if c.startswith('pct_sin_')]
    if pct_sin_cols:
        result_df['indice_brecha_servicios'] = result_df[pct_sin_cols].mean(axis=1).round(2)

    result_df.to_csv('tarea5_servicios_basicos.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ Exportado: tarea5_servicios_basicos.csv ({len(result_df)} comunas)")


# ══════════════════════════════════════════════════════════════════════════════
# TAREA 6 — Indicador de Desarrollo Compuesto
# ══════════════════════════════════════════════════════════════════════════════
def tarea6_indicador_desarrollo(df_per, df_hog, df_viv):
    print("\n=== TAREA 6: Indicador de Desarrollo Compuesto ===")

    # Columnas de comuna
    col_com_per = detectar_columna(df_per, [COL_COMUNA, 'comuna', 'nombre_comuna'], 'comuna_personas')
    col_com_hog = detectar_columna(df_hog, [COL_COMUNA, 'comuna', 'nombre_comuna'], 'comuna_hogares')
    col_com_viv = detectar_columna(df_viv, [COL_COMUNA, 'comuna', 'nombre_comuna'], 'comuna_vivienda')
    col_prov_per = detectar_columna(df_per, [COL_PROVINCIA, 'provincia', 'nombre_provincia'], 'provincia')

    # — Componente 1: Índice de envejecimiento (% personas >= 65 años) —
    col_edad = detectar_columna(df_per, [COL_EDAD, 'p09', 'edad'], 'edad')
    env_df = None
    if col_com_per and col_edad:
        env_agg = df_per.groupby([col_com_per]).apply(
            lambda x: (x[col_edad] >= 65).sum() / len(x) * 100
        ).reset_index(name='pct_mayores65')
        env_df = env_agg.rename(columns={col_com_per: 'comuna'})

    # — Componente 2: Índice de educación baja (% sin educación o básica incompleta) —
    col_educ = detectar_columna(df_per, [COL_EDUC, 'p14', 'nivel_educ'], 'nivel_educativo')
    educ_df = None
    if col_com_per and col_educ:
        educ_agg = df_per.groupby([col_com_per]).apply(
            lambda x: (x[col_educ].isin([0, 1, 2])).sum() / len(x) * 100
        ).reset_index(name='pct_educ_baja')
        educ_df = educ_agg.rename(columns={col_com_per: 'comuna'})

    # — Componente 3: Índice de hacinamiento (% hogares hacinados) —
    col_per_hog = detectar_columna(df_hog, [COL_N_PERSONAS, 'n_personas', 'cant_per', 'tot_per'], 'n_personas_hogar')
    col_cuar    = detectar_columna(df_hog, [COL_N_CUARTOS, 'n_cuartos', 'cant_cuar', 'cuartos'], 'n_cuartos')
    hac_df = None
    if col_com_hog and col_per_hog and col_cuar:
        df_h = df_hog.copy()
        df_h = df_h[df_h[col_cuar].notna() & (df_h[col_cuar] > 0)]
        df_h['hacinado'] = (df_h[col_per_hog] / df_h[col_cuar]) >= 2.5
        hac_agg = df_h.groupby([col_com_hog]).apply(
            lambda x: x['hacinado'].sum() / len(x) * 100
        ).reset_index(name='pct_hacinamiento')
        hac_df = hac_agg.rename(columns={col_com_hog: 'comuna'})

    # — Componente 4: Brecha de servicios básicos (% viviendas sin acceso) —
    serv_df = None
    col_agua = detectar_columna(df_viv, [COL_AGUA, 'p03', 'agua', 'proced_agua'], 'agua')
    col_elec = detectar_columna(df_viv, [COL_ELECTRIC, 'p04', 'electricidad'], 'electricidad')
    col_alc  = detectar_columna(df_viv, [COL_ALCANT, 'p05', 'alcantarillado'], 'alcantarillado')
    if col_com_viv:
        brechas = []
        for col_s in [c for c in [col_agua, col_elec, col_alc] if c]:
            b = df_viv.groupby([col_com_viv]).apply(
                lambda x, c=col_s: (x[c] != 1).sum() / len(x) * 100
            ).reset_index(name=f'pct_sin_{col_s}')
            brechas.append(b.rename(columns={col_com_viv: 'comuna'}))
        if brechas:
            serv_df = brechas[0]
            for b in brechas[1:]:
                serv_df = serv_df.merge(b, on='comuna', how='outer')
            pct_sin_cols = [c for c in serv_df.columns if c.startswith('pct_sin_')]
            serv_df['pct_brecha_servicios'] = serv_df[pct_sin_cols].mean(axis=1)

    # — Merge de componentes —
    componentes = [df for df in [env_df, educ_df, hac_df] if df is not None]
    if not componentes:
        print("  No hay suficientes componentes para calcular el indicador.")
        return

    indicador = componentes[0]
    for df_comp in componentes[1:]:
        indicador = indicador.merge(df_comp, on='comuna', how='outer')

    if serv_df is not None and 'pct_brecha_servicios' in serv_df.columns:
        indicador = indicador.merge(serv_df[['comuna', 'pct_brecha_servicios']], on='comuna', how='outer')

    # Agregar nombre de provincia
    if col_prov_per and col_com_per:
        prov_map = df_per[[col_com_per, col_prov_per]].drop_duplicates()
        prov_map.columns = ['comuna', 'provincia']
        indicador = indicador.merge(prov_map, on='comuna', how='left')

    # — Normalización Min-Max (0-100) y cálculo del indicador compuesto —
    componentes_cols = [c for c in ['pct_mayores65', 'pct_educ_baja', 'pct_hacinamiento', 'pct_brecha_servicios']
                        if c in indicador.columns]

    for col in componentes_cols:
        col_min = indicador[col].min()
        col_max = indicador[col].max()
        if col_max > col_min:
            indicador[f'{col}_norm'] = ((indicador[col] - col_min) / (col_max - col_min) * 100).round(2)
        else:
            indicador[f'{col}_norm'] = 0

    norm_cols = [f'{c}_norm' for c in componentes_cols if f'{c}_norm' in indicador.columns]
    if norm_cols:
        indicador['indicador_desarrollo_compuesto'] = indicador[norm_cols].mean(axis=1).round(2)

        # Clasificación de prioridad de política pública
        q33 = indicador['indicador_desarrollo_compuesto'].quantile(0.33)
        q66 = indicador['indicador_desarrollo_compuesto'].quantile(0.66)

        def clasificar_prioridad(val):
            if val >= q66:
                return 'Alta prioridad'
            elif val >= q33:
                return 'Media prioridad'
            else:
                return 'Baja prioridad'

        indicador['prioridad_politica_publica'] = indicador['indicador_desarrollo_compuesto'].apply(clasificar_prioridad)

    indicador = indicador.round(3)
    indicador.to_csv('tarea6_indicador_desarrollo.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ Exportado: tarea6_indicador_desarrollo.csv ({len(indicador)} comunas)")
    if 'indicador_desarrollo_compuesto' in indicador.columns:
        print("\n  TOP 10 comunas con mayor prioridad:")
        top10 = indicador.nlargest(10, 'indicador_desarrollo_compuesto')[
            ['comuna'] + (['provincia'] if 'provincia' in indicador.columns else []) +
            ['indicador_desarrollo_compuesto', 'prioridad_politica_publica']
        ]
        print(top10.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  PREPARACIÓN DE DATOS PARA POWER BI - TALLER 2")
    print("  Censo 2024 - Región de Valparaíso")
    print("=" * 60)

    # Cargar datos
    print("\n[1/3] Cargando Base de Personas...")
    df_per = cargar_csv(PERSONAS_FILE, 'personas_valpo1.csv')

    print("\n[2/3] Cargando Base de Hogares...")
    df_hog = cargar_csv(HOGARES_FILE, 'hogares_valpo1.csv')

    print("\n[3/3] Cargando Base de Viviendas...")
    df_viv = cargar_csv(VIVIENDA_FILE, 'vivienda_valpo1.csv')

    # Normalizar nombres de columnas
    for df in [df_per, df_hog, df_viv]:
        if df is not None:
            normalizar_columnas(df)

    # Mostrar columnas disponibles para diagnóstico
    print("\n--- Columnas disponibles ---")
    if df_per is not None:
        print(f"PERSONAS : {list(df_per.columns)}")
    if df_hog is not None:
        print(f"HOGARES  : {list(df_hog.columns)}")
    if df_viv is not None:
        print(f"VIVIENDA : {list(df_viv.columns)}")

    print("\n--- Procesando tareas ---")

    if df_hog is not None:
        tarea3_hacinamiento(df_hog)

    if df_per is not None:
        tarea4_educacion_actividad(df_per)

    if df_viv is not None:
        tarea5_servicios_basicos(df_viv)

    if all(d is not None for d in [df_per, df_hog, df_viv]):
        tarea6_indicador_desarrollo(df_per, df_hog, df_viv)
    else:
        print("\n[AVISO] Tarea 6 requiere los 3 archivos. Verifica que todos estén disponibles.")

    print("\n" + "=" * 60)
    print("  ✓ PROCESO COMPLETADO")
    print("  Archivos generados:")
    for f in ['tarea3_hacinamiento.csv', 'tarea3_hacinamiento_detalle.csv',
              'tarea4_educacion_actividad.csv', 'tarea4_educacion_actividad_pct.csv',
              'tarea5_servicios_basicos.csv', 'tarea6_indicador_desarrollo.csv']:
        if os.path.exists(f):
            size = os.path.getsize(f) / 1024
            print(f"    {f} ({size:.1f} KB)")
    print("=" * 60)
    print("\nSiguiente paso: Importa estos CSVs en Power BI")
    print("(Inicio -> Obtener datos -> Texto/CSV)")


if __name__ == '__main__':
    main()
