# -*- coding: utf-8 -*-
"""
Taller 2 - Preparación de datos para Power BI
Tareas 3 a 6 - Censo 2024 Región de Valparaíso
"""

import pandas as pd
import numpy as np
import os
import sys

def _get_script_dir():
    for candidate in [
        getattr(sys.modules['__main__'], '__file__', None),
        sys.argv[0] if sys.argv else None,
        __file__,
    ]:
        if candidate:
            d = os.path.dirname(os.path.abspath(candidate))
            if os.path.isdir(d):
                return d
    return os.getcwd()

SCRIPT_DIR = _get_script_dir()
os.chdir(SCRIPT_DIR)

# ── Nombres reales de columnas (confirmados del debug) ──
COL_COMUNA    = 'comuna'
COL_PROVINCIA = 'provincia'
COL_EDAD      = 'edad'
COL_SEXO      = 'sexo'
COL_EDUC      = 'cine11'
COL_ACTIVIDAD = 'sit_fuerza_trabajo'
COL_HACI      = 'indice_hacinamiento'   # en vivienda, ya calculado
COL_NPER_VIV  = 'cant_per'             # personas en vivienda
COL_NDORM     = 'p5_num_dormitorios'
COL_AGUA      = 'p6_fuente_agua'
COL_ELEC      = 'p9_fuente_elect'
COL_SHG       = 'p8_serv_hig'

# ── Tabla de nombres de comunas (Región de Valparaíso, códigos INE) ──
NOMBRES_COMUNAS = {
    5101:'Valparaíso', 5102:'Casablanca', 5103:'Concón', 5104:'Juan Fernández',
    5105:'Puchuncaví', 5107:'Quintero', 5109:'Viña del Mar',
    5201:'Isla de Pascua',
    5301:'Los Andes', 5302:'Calle Larga', 5303:'Rinconada', 5304:'San Esteban',
    5401:'La Ligua', 5402:'Cabildo', 5403:'Papudo', 5404:'Petorca', 5405:'Zapallar',
    5501:'Quillota', 5502:'Calera', 5503:'Hijuelas', 5504:'La Cruz', 5506:'Nogales',
    5601:'San Antonio', 5602:'Algarrobo', 5603:'Cartagena', 5604:'El Quisco',
    5605:'El Tabo', 5606:'Santo Domingo',
    5701:'San Felipe', 5702:'Catemu', 5703:'Llay-Llay', 5704:'Panquehue',
    5705:'Putaendo', 5706:'Santa María',
    5801:'Quilpué', 5802:'Limache', 5803:'Olmué', 5804:'Villa Alemana',
}

NOMBRES_PROVINCIAS = {
    51:'Valparaíso', 52:'Isla de Pascua', 53:'Los Andes', 54:'Petorca',
    55:'Quillota', 56:'San Antonio', 57:'San Felipe de Aconcagua', 58:'Marga Marga',
}

# ── Mapas de etiquetas ──
MAPA_CINE = {
    -99:'Sin dato',
    0:'0. Sin nivel', 1:'1. Parvularia', 2:'2. Básica',
    3:'3. Media (1° ciclo)', 4:'4. Media (2° ciclo)',
    5:'5. Técnico sup. (ciclo corto)', 6:'6. Universitaria/Licenciatura',
    7:'7. Magíster', 8:'8. Doctorado', 9:'9. No informa',
    10:'10. Técnico nivel superior', 11:'11. Universitaria (en curso)',
    12:'12. Sin nivel (≥15 años)',
}

MAPA_ACTIVIDAD = {
    -99:'Sin dato',
    1:'Ocupado', 2:'Desocupado', 3:'Inactivo', 9:'No aplica (<15 años)',
}

MAPA_AGUA = {
    1:'Red pública', 2:'Pozo/noria', 3:'Camión aljibe',
    4:'Río/vertiente', 5:'Otro',
}

MAPA_ELEC = {
    1:'Red pública', 2:'Generador/panel solar', 3:'Sin electricidad',
}

MAPA_SHG = {
    1:'WC - alcantarillado', 2:'WC - fosa séptica',
    3:'Letrina/cajón', 4:'Sin servicio higiénico',
}


def cargar_csv(filename):
    if not os.path.exists(filename):
        print(f"  ERROR: No se encontró {filename}")
        return None
    print(f"  Cargando {filename} ...")
    with open(filename, 'r', encoding='utf-8', errors='replace') as fh:
        primera = fh.readline()
    sep = ';' if primera.count(';') > primera.count(',') else ','
    df = pd.read_csv(filename, sep=sep, encoding='utf-8',
                     encoding_errors='replace', low_memory=False)
    print(f"  -> {len(df):,} filas, {len(df.columns)} columnas")
    return df


def agregar_nombres(df, col_comuna=COL_COMUNA, col_provincia=COL_PROVINCIA):
    """Agrega columnas con nombres legibles de provincia y comuna."""
    if col_provincia in df.columns:
        df['nombre_provincia'] = df[col_provincia].map(NOMBRES_PROVINCIAS).fillna(df[col_provincia].astype(str))
    if col_comuna in df.columns:
        df['nombre_comuna'] = df[col_comuna].map(NOMBRES_COMUNAS).fillna(df[col_comuna].astype(str))
    return df


# ══════════════════════════════════════════════════════════════════════════════
# TAREA 3 — Hacinamiento (fuente: VIVIENDA)
# ══════════════════════════════════════════════════════════════════════════════
def tarea3_hacinamiento(df_viv):
    print("\n=== TAREA 3: Hacinamiento ===")
    df = df_viv.copy()
    agregar_nombres(df)

    # El índice ya viene calculado en el CSV de vivienda
    if COL_HACI not in df.columns:
        print("  ERROR: columna indice_hacinamiento no encontrada en vivienda.")
        return

    def clasificar(idx):
        if pd.isna(idx):   return 'Sin dato'
        if idx <= 2.4:     return 'Sin hacinamiento'
        elif idx <= 3.4:   return 'Hacinamiento medio'
        elif idx <= 4.9:   return 'Hacinamiento alto'
        else:              return 'Hacinamiento crítico'

    df['categoria_hacinamiento'] = df[COL_HACI].apply(clasificar)
    group = ['nombre_provincia', 'nombre_comuna']

    resumen = df.groupby(group).agg(
        total_viviendas=(COL_HACI, 'count'),
        indice_hacinamiento_promedio=(COL_HACI, 'mean'),
        promedio_personas=('cant_per', 'mean') if 'cant_per' in df.columns else (COL_HACI, 'count'),
        promedio_dormitorios=(COL_NDORM, 'mean') if COL_NDORM in df.columns else (COL_HACI, 'count'),
        sin_hacinamiento=('categoria_hacinamiento', lambda x: (x=='Sin hacinamiento').sum()),
        hacinamiento_medio=('categoria_hacinamiento', lambda x: (x=='Hacinamiento medio').sum()),
        hacinamiento_alto=('categoria_hacinamiento', lambda x: (x=='Hacinamiento alto').sum()),
        hacinamiento_critico=('categoria_hacinamiento', lambda x: (x=='Hacinamiento crítico').sum()),
    ).reset_index()

    resumen['pct_hacinados'] = (
        (resumen['hacinamiento_medio'] + resumen['hacinamiento_alto'] + resumen['hacinamiento_critico'])
        / resumen['total_viviendas'] * 100
    ).round(2)
    resumen['indice_hacinamiento_promedio'] = resumen['indice_hacinamiento_promedio'].round(3)

    resumen.to_csv('tarea3_hacinamiento.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ tarea3_hacinamiento.csv ({len(resumen)} comunas)")

    # Detalle por vivienda para scatter plot
    cols_det = [c for c in ['nombre_provincia','nombre_comuna', COL_HACI,
                             'cant_per', COL_NDORM, 'categoria_hacinamiento'] if c in df.columns]
    df[cols_det].to_csv('tarea3_hacinamiento_detalle.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ tarea3_hacinamiento_detalle.csv ({len(df):,} viviendas)")


# ══════════════════════════════════════════════════════════════════════════════
# TAREA 4 — Educación y Condición de Actividad (fuente: PERSONAS)
# ══════════════════════════════════════════════════════════════════════════════
def tarea4_educacion_actividad(df_per):
    print("\n=== TAREA 4: Educación y Condición de Actividad ===")
    df = df_per.copy()
    agregar_nombres(df)

    if COL_EDUC not in df.columns or COL_ACTIVIDAD not in df.columns:
        print(f"  ERROR: faltan columnas {COL_EDUC} o {COL_ACTIVIDAD}")
        return

    # Solo población >= 15 años para análisis laboral
    df15 = df[df[COL_EDAD] >= 15].copy()

    df15['nivel_educativo'] = df15[COL_EDUC].map(MAPA_CINE).fillna(df15[COL_EDUC].astype(str))
    df15['condicion_actividad'] = df15[COL_ACTIVIDAD].map(MAPA_ACTIVIDAD).fillna(df15[COL_ACTIVIDAD].astype(str))

    group = ['nombre_provincia', 'nombre_comuna', 'nivel_educativo', 'condicion_actividad']

    resultado = df15.groupby(group).size().reset_index(name='n_personas')
    resultado.to_csv('tarea4_educacion_actividad.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ tarea4_educacion_actividad.csv ({len(resultado):,} filas)")

    # Con porcentajes
    totales = df15.groupby(['nombre_provincia','nombre_comuna','nivel_educativo']).size().reset_index(name='total_nivel')
    pct = resultado.merge(totales, on=['nombre_provincia','nombre_comuna','nivel_educativo'])
    pct['porcentaje'] = (pct['n_personas'] / pct['total_nivel'] * 100).round(2)
    pct.to_csv('tarea4_educacion_actividad_pct.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ tarea4_educacion_actividad_pct.csv")


# ══════════════════════════════════════════════════════════════════════════════
# TAREA 5 — Servicios Básicos (fuente: VIVIENDA)
# ══════════════════════════════════════════════════════════════════════════════
def tarea5_servicios_basicos(df_viv):
    print("\n=== TAREA 5: Servicios Básicos ===")
    df = df_viv.copy()
    agregar_nombres(df)
    group = ['nombre_provincia', 'nombre_comuna']

    res = df.groupby(group).size().reset_index(name='total_viviendas')

    # Agua: código 1 = red pública
    if COL_AGUA in df.columns:
        a = df.groupby(group).apply(lambda x: (x[COL_AGUA]==1).sum()).reset_index(name='con_agua_red_publica')
        res = res.merge(a, on=group)
        res['pct_agua'] = (res['con_agua_red_publica'] / res['total_viviendas'] * 100).round(2)
        res['pct_sin_agua'] = (100 - res['pct_agua']).round(2)

    # Electricidad: código 1 = red pública
    if COL_ELEC in df.columns:
        e = df.groupby(group).apply(lambda x: (x[COL_ELEC]==1).sum()).reset_index(name='con_electricidad_red')
        res = res.merge(e, on=group)
        res['pct_electricidad'] = (res['con_electricidad_red'] / res['total_viviendas'] * 100).round(2)
        res['pct_sin_electricidad'] = (100 - res['pct_electricidad']).round(2)

    # Servicio higiénico: código 1 = WC conectado a alcantarillado
    if COL_SHG in df.columns:
        s = df.groupby(group).apply(lambda x: (x[COL_SHG]==1).sum()).reset_index(name='con_alcantarillado')
        res = res.merge(s, on=group)
        res['pct_alcantarillado'] = (res['con_alcantarillado'] / res['total_viviendas'] * 100).round(2)
        res['pct_sin_alcantarillado'] = (100 - res['pct_alcantarillado']).round(2)

    pct_sin = [c for c in res.columns if c.startswith('pct_sin_')]
    if pct_sin:
        res['indice_brecha_servicios'] = res[pct_sin].mean(axis=1).round(2)

    res.to_csv('tarea5_servicios_basicos.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ tarea5_servicios_basicos.csv ({len(res)} comunas)")

    # Detalle con etiquetas para gráficos
    for col, mapa, nombre in [(COL_AGUA, MAPA_AGUA, 'agua'), (COL_ELEC, MAPA_ELEC, 'electricidad'), (COL_SHG, MAPA_SHG, 'serv_hig')]:
        if col in df.columns:
            df[f'label_{nombre}'] = df[col].map(mapa).fillna(df[col].astype(str))

    cols_det = [c for c in ['nombre_provincia','nombre_comuna'] +
                [f'label_{n}' for n in ['agua','electricidad','serv_hig']] if c in df.columns]
    df[cols_det].to_csv('tarea5_servicios_detalle.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ tarea5_servicios_detalle.csv")


# ══════════════════════════════════════════════════════════════════════════════
# TAREA 6 — Indicador de Desarrollo Compuesto
# ══════════════════════════════════════════════════════════════════════════════
def tarea6_indicador_desarrollo(df_per, df_viv):
    print("\n=== TAREA 6: Indicador de Desarrollo Compuesto ===")

    per = df_per.copy()
    viv = df_viv.copy()
    agregar_nombres(per)
    agregar_nombres(viv)
    group_per = ['nombre_provincia', 'nombre_comuna']
    group_viv = ['nombre_provincia', 'nombre_comuna']

    # 1. Envejecimiento: % personas >= 65
    env = per.groupby(group_per).apply(
        lambda x: (x[COL_EDAD] >= 65).sum() / len(x) * 100
    ).reset_index(name='pct_mayores65')

    # 2. Educación baja: % con CINE 0 (sin nivel) o 1 (parvularia) o 2 (básica)
    educ = per.groupby(group_per).apply(
        lambda x: x[COL_EDUC].isin([0, 1, 2]).sum() / len(x) * 100
    ).reset_index(name='pct_educ_baja')

    # 3. Hacinamiento: % viviendas con indice >= 2.5
    hac = viv.groupby(group_viv).apply(
        lambda x: (x[COL_HACI] >= 2.5).sum() / len(x) * 100
    ).reset_index(name='pct_hacinamiento')

    # 4. Brecha de servicios: promedio de % sin acceso a los 3 servicios
    brecha_cols = []
    for col in [COL_AGUA, COL_ELEC, COL_SHG]:
        if col in viv.columns:
            b = viv.groupby(group_viv).apply(
                lambda x, c=col: (x[c] != 1).sum() / len(x) * 100
            ).reset_index(name=f'pct_sin_{col}')
            brecha_cols.append(b)

    ind = env.merge(educ, on=group_per, how='outer')
    ind = ind.merge(hac, on=group_per, how='outer')
    for b in brecha_cols:
        ind = ind.merge(b, on=group_per, how='outer')

    pct_sin_cols = [c for c in ind.columns if c.startswith('pct_sin_')]
    if pct_sin_cols:
        ind['pct_brecha_servicios'] = ind[pct_sin_cols].mean(axis=1)

    # Normalización Min-Max 0–100 (100 = peor situación)
    dims = [c for c in ['pct_mayores65','pct_educ_baja','pct_hacinamiento','pct_brecha_servicios'] if c in ind.columns]
    for c in dims:
        mn, mx = ind[c].min(), ind[c].max()
        ind[f'{c}_norm'] = ((ind[c]-mn)/(mx-mn)*100).round(2) if mx > mn else 0

    norm_cols = [f'{c}_norm' for c in dims]
    ind['indicador_desarrollo_compuesto'] = ind[norm_cols].mean(axis=1).round(2)

    q33 = ind['indicador_desarrollo_compuesto'].quantile(0.33)
    q66 = ind['indicador_desarrollo_compuesto'].quantile(0.66)
    ind['prioridad_politica_publica'] = ind['indicador_desarrollo_compuesto'].apply(
        lambda v: 'Alta prioridad' if v >= q66 else ('Media prioridad' if v >= q33 else 'Baja prioridad')
    )

    ind.round(3).to_csv('tarea6_indicador_desarrollo.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ tarea6_indicador_desarrollo.csv ({len(ind)} comunas)")

    print("\n  TOP 10 comunas prioritarias:")
    cols_show = ['nombre_provincia','nombre_comuna'] + dims + ['indicador_desarrollo_compuesto','prioridad_politica_publica']
    cols_show = [c for c in cols_show if c in ind.columns]
    print(ind.nlargest(10,'indicador_desarrollo_compuesto')[cols_show].to_string(index=False))


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  PREPARACIÓN DE DATOS PARA POWER BI - TALLER 2")
    print("  Censo 2024 - Región de Valparaíso")
    print("=" * 60)
    print(f"\n  Carpeta: {SCRIPT_DIR}")

    # Para regenerar solo tarea4 más rápido, solo carga personas
    solo_tarea4 = '--solo-tarea4' in sys.argv

    print("\n[1] Cargando personas...")
    df_per = cargar_csv('personas_valpo.csv')
    if df_per is None:
        print("\nERROR: falta personas_valpo.csv. Abortando.")
        input("\nPresiona Enter para cerrar...")
        return

    if solo_tarea4:
        print("\n--- Regenerando solo Tarea 4 ---")
        tarea4_educacion_actividad(df_per)
    else:
        print("\n[2] Cargando vivienda...")
        df_viv = cargar_csv('vivienda_valpo.csv')
        if df_viv is None:
            print("\nERROR: falta vivienda_valpo.csv. Abortando.")
            input("\nPresiona Enter para cerrar...")
            return
        print("\n--- Procesando todo ---")
        tarea3_hacinamiento(df_viv)
        tarea4_educacion_actividad(df_per)
        tarea5_servicios_basicos(df_viv)
        tarea6_indicador_desarrollo(df_per, df_viv)

    print("\n" + "=" * 60)
    print("  ✓ LISTO — Archivos generados:")
    for f in ['tarea3_hacinamiento.csv','tarea3_hacinamiento_detalle.csv',
              'tarea4_educacion_actividad.csv','tarea4_educacion_actividad_pct.csv',
              'tarea5_servicios_basicos.csv','tarea5_servicios_detalle.csv',
              'tarea6_indicador_desarrollo.csv']:
        if os.path.exists(f):
            print(f"    ✓ {f}  ({os.path.getsize(f)/1024:.1f} KB)")
        else:
            print(f"    ✗ {f}  (no generado)")
    print("=" * 60)
    input("\nPresiona Enter para cerrar...")


if __name__ == '__main__':
    main()
