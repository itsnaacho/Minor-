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
COL_DISTRIB   = 'p7_distrib_agua'   # distribución dentro de la vivienda (tarea_1 lo exige)
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
    1:'1. Sin educación', 2:'2. Básica',
    3:'3. Media baja', 4:'4. Media alta',
    5:'5. Post-secundaria', 6:'6. Técnica superior',
    7:'7. Universitaria', 8:'8. Postgrado',
}

MAPA_ACTIVIDAD = {
    1:'Ocupado', 2:'Desocupado', 3:'Inactivo',
}

# indice_hacinamiento en el Censo 2024 es CATEGÓRICO:
# 1 = Sin hacinamiento, 2 = Hacinamiento medio, 3 = Hacinamiento crítico
MAPA_HACINAMIENTO = {
    1:'Sin hacinamiento', 2:'Hacinamiento medio', 3:'Hacinamiento crítico',
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
    if col_provincia in df.columns:
        df['nombre_provincia'] = df[col_provincia].map(NOMBRES_PROVINCIAS).fillna(df[col_provincia].astype(str))
    if col_comuna in df.columns:
        df['nombre_comuna'] = df[col_comuna].map(NOMBRES_COMUNAS).fillna(df[col_comuna].astype(str))
    return df


def calcular_top10(df_per):
    """Devuelve set de nombres de las 10 comunas más pobladas (igual que tarea_1)."""
    top10_codigos = df_per[COL_COMUNA].value_counts().head(10).index.tolist()
    top10_nombres = {NOMBRES_COMUNAS.get(c, str(c)) for c in top10_codigos}
    print(f"\n  Top 10 comunas más pobladas: {sorted(top10_nombres)}")
    return top10_nombres


def agregar_top10(df_resumen, top10_nombres):
    """Agrega columna es_top10 a un dataframe con columna nombre_comuna."""
    df_resumen['es_top10'] = df_resumen['nombre_comuna'].isin(top10_nombres).map(
        {True: 'Top 10', False: 'Resto región'}
    )
    return df_resumen


# ══════════════════════════════════════════════════════════════════════════════
# TAREA 3 — Hacinamiento (fuente: VIVIENDA)
# ══════════════════════════════════════════════════════════════════════════════
def tarea3_hacinamiento(df_viv, top10_nombres=None):
    print("\n=== TAREA 3: Hacinamiento ===")
    df = df_viv.copy()
    agregar_nombres(df)

    if COL_HACI not in df.columns:
        print("  ERROR: columna indice_hacinamiento no encontrada en vivienda.")
        return

    # indice_hacinamiento es CATEGÓRICO: 1=Sin hacinamiento, 2=Medio, 3=Crítico
    # Se excluyen -99 (no aplica) y NaN
    df = df[df[COL_HACI].isin([1, 2, 3])].copy()
    df['categoria_hacinamiento'] = df[COL_HACI].map(MAPA_HACINAMIENTO)

    group = ['nombre_provincia', 'nombre_comuna']

    agg = {'total_viviendas': (COL_HACI, 'count')}
    if 'cant_per' in df.columns:
        agg['promedio_personas'] = ('cant_per', 'mean')
    if COL_NDORM in df.columns:
        agg['promedio_dormitorios'] = (COL_NDORM, 'mean')
    agg['sin_hacinamiento']    = ('categoria_hacinamiento', lambda x: (x=='Sin hacinamiento').sum())
    agg['hacinamiento_medio']  = ('categoria_hacinamiento', lambda x: (x=='Hacinamiento medio').sum())
    agg['hacinamiento_critico']= ('categoria_hacinamiento', lambda x: (x=='Hacinamiento crítico').sum())

    resumen = df.groupby(group).agg(**agg).reset_index()

    resumen['pct_hacinados'] = (
        (resumen['hacinamiento_medio'] + resumen['hacinamiento_critico'])
        / resumen['total_viviendas'] * 100
    ).round(2)

    if 'promedio_personas' in resumen.columns:
        resumen['promedio_personas'] = resumen['promedio_personas'].round(2)
    if 'promedio_dormitorios' in resumen.columns:
        resumen['promedio_dormitorios'] = resumen['promedio_dormitorios'].round(2)

    if top10_nombres:
        agregar_top10(resumen, top10_nombres)
    resumen.to_csv('tarea3_hacinamiento.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ tarea3_hacinamiento.csv ({len(resumen)} comunas)")
    print("  Top 5 por % hacinados (todas las comunas):")
    print(resumen.nlargest(5, 'pct_hacinados')[['nombre_comuna','pct_hacinados','promedio_personas']].to_string(index=False))
    if top10_nombres:
        top10_df = resumen[resumen['es_top10']=='Top 10']
        print("  Top 5 por % hacinados (solo top 10 comunas):")
        print(top10_df.nlargest(5, 'pct_hacinados')[['nombre_comuna','pct_hacinados','promedio_personas']].to_string(index=False))

    cols_det = [c for c in ['nombre_provincia','nombre_comuna', COL_HACI,
                             'cant_per', COL_NDORM, 'categoria_hacinamiento'] if c in df.columns]
    df[cols_det].to_csv('tarea3_hacinamiento_detalle.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ tarea3_hacinamiento_detalle.csv ({len(df):,} viviendas)")


# ══════════════════════════════════════════════════════════════════════════════
# TAREA 4 — Educación y Condición de Actividad (fuente: PERSONAS)
# ══════════════════════════════════════════════════════════════════════════════
def tarea4_educacion_actividad(df_per, top10_nombres=None):
    print("\n=== TAREA 4: Educación y Condición de Actividad ===")
    df = df_per.copy()
    agregar_nombres(df)

    if COL_EDUC not in df.columns or COL_ACTIVIDAD not in df.columns:
        print(f"  ERROR: faltan columnas {COL_EDUC} o {COL_ACTIVIDAD}")
        return

    # Solo población >= 15 años, excluir -99 (no aplica) en ambas variables
    df15 = df[
        (df[COL_EDAD] >= 15) &
        (df[COL_EDUC].notna()) & (df[COL_EDUC] != -99) & (df[COL_EDUC] > 0) &
        (df[COL_ACTIVIDAD].notna()) & (df[COL_ACTIVIDAD] != -99) &
        (df[COL_ACTIVIDAD].isin([1, 2, 3]))
    ].copy()

    # Códigos 8+ se agrupan como Postgrado (igual que tarea_1)
    df15['_cine_agrup'] = df15[COL_EDUC].apply(lambda x: min(int(x), 8) if pd.notna(x) else np.nan)
    df15['nivel_educativo']    = df15['_cine_agrup'].map(MAPA_CINE).fillna('Sin dato')
    df15['condicion_actividad'] = df15[COL_ACTIVIDAD].map(MAPA_ACTIVIDAD).fillna('Sin dato')

    group = ['nombre_provincia', 'nombre_comuna', 'nivel_educativo', 'condicion_actividad']

    resultado = df15.groupby(group).size().reset_index(name='n_personas')
    if top10_nombres:
        agregar_top10(resultado, top10_nombres)
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
def tarea5_servicios_basicos(df_viv, top10_nombres=None):
    print("\n=== TAREA 5: Servicios Básicos ===")
    # Solo viviendas con dato válido en los 4 servicios (igual que tarea_1)
    cols_serv = [c for c in [COL_AGUA, COL_DISTRIB, COL_SHG, COL_ELEC] if c in df_viv.columns]
    df = df_viv.copy()
    agregar_nombres(df)
    for c in cols_serv:
        df = df[df[c].notna() & (df[c] != -99)]

    group = ['nombre_provincia', 'nombre_comuna']
    res = df.groupby(group).size().reset_index(name='total_viviendas')

    # Agua potable: red pública (p6==1) Y distribuida dentro de la vivienda (p7==1)
    tiene_agua = (df[COL_AGUA] == 1)
    if COL_DISTRIB in df.columns:
        tiene_agua = tiene_agua & (df[COL_DISTRIB] == 1)
    df['_tiene_agua'] = tiene_agua.astype(int)
    a = df.groupby(group)['_tiene_agua'].sum().reset_index(name='con_agua_potable')
    res = res.merge(a, on=group)
    res['pct_agua'] = (res['con_agua_potable'] / res['total_viviendas'] * 100).round(2)
    res['pct_sin_agua'] = (100 - res['pct_agua']).round(2)

    # Electricidad: red pública (p9==1)
    df['_tiene_elect'] = (df[COL_ELEC] == 1).astype(int)
    e = df.groupby(group)['_tiene_elect'].sum().reset_index(name='con_electricidad_red')
    res = res.merge(e, on=group)
    res['pct_electricidad'] = (res['con_electricidad_red'] / res['total_viviendas'] * 100).round(2)
    res['pct_sin_electricidad'] = (100 - res['pct_electricidad']).round(2)

    # Alcantarillado: WC conectado a red (p8==1)
    df['_tiene_alc'] = (df[COL_SHG] == 1).astype(int)
    s = df.groupby(group)['_tiene_alc'].sum().reset_index(name='con_alcantarillado')
    res = res.merge(s, on=group)
    res['pct_alcantarillado'] = (res['con_alcantarillado'] / res['total_viviendas'] * 100).round(2)
    res['pct_sin_alcantarillado'] = (100 - res['pct_alcantarillado']).round(2)

    # Acceso completo: tiene los 3 servicios (igual que tarea_1)
    df['_acceso_completo'] = (df['_tiene_agua'] & df['_tiene_elect'] & df['_tiene_alc']).astype(int)
    ac = df.groupby(group)['_acceso_completo'].sum().reset_index(name='con_acceso_completo')
    res = res.merge(ac, on=group)
    res['pct_acceso_completo'] = (res['con_acceso_completo'] / res['total_viviendas'] * 100).round(2)
    res['indice_brecha_servicios'] = (100 - res['pct_acceso_completo']).round(2)

    if top10_nombres:
        agregar_top10(res, top10_nombres)
    res.to_csv('tarea5_servicios_basicos.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ tarea5_servicios_basicos.csv ({len(res)} comunas)")

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
def tarea6_indicador_desarrollo(df_per, df_viv, top10_nombres=None):
    print("\n=== TAREA 6: Indicador de Desarrollo Compuesto ===")

    per = df_per.copy()
    viv = df_viv.copy()
    agregar_nombres(per)
    agregar_nombres(viv)
    group_per = ['nombre_provincia', 'nombre_comuna']
    group_viv = ['nombre_provincia', 'nombre_comuna']

    # 1. Envejecimiento: % personas >= 65
    per['_mayor65'] = (per[COL_EDAD] >= 65).astype(int)
    env = per.groupby(group_per)['_mayor65'].agg(
        pct_mayores65=lambda x: x.sum() / len(x) * 100
    ).reset_index()

    # 2. Educación baja: % con cine11 <= 2, excluyendo -99 y 0 (igual que tarea_1)
    per_edu = per[per[COL_EDUC].notna() & (per[COL_EDUC] != -99) & (per[COL_EDUC] > 0)].copy()
    per_edu['_educ_baja'] = per_edu[COL_EDUC].isin([1, 2]).astype(int)
    educ = per_edu.groupby(group_per)['_educ_baja'].agg(
        pct_educ_baja=lambda x: x.sum() / len(x) * 100
    ).reset_index()

    # 3. Hacinamiento: % viviendas con código 2 (medio) o 3 (crítico)
    viv_hac = viv[viv[COL_HACI].isin([1, 2, 3])].copy()
    viv_hac['_hacinado'] = (viv_hac[COL_HACI] >= 2).astype(int)
    hac = viv_hac.groupby(group_viv)['_hacinado'].agg(
        pct_hacinamiento=lambda x: x.sum() / len(x) * 100
    ).reset_index()

    # 4. Brecha de servicios: % sin acceso completo (igual que tarea_1: los 3 servicios juntos)
    cols_serv6 = [c for c in [COL_AGUA, COL_DISTRIB, COL_SHG, COL_ELEC] if c in viv.columns]
    viv6 = viv.copy()
    for c in cols_serv6:
        viv6 = viv6[viv6[c].notna() & (viv6[c] != -99)]

    tiene_agua6 = (viv6[COL_AGUA] == 1)
    if COL_DISTRIB in viv6.columns:
        tiene_agua6 = tiene_agua6 & (viv6[COL_DISTRIB] == 1)
    viv6['_acceso_completo'] = (
        tiene_agua6 & (viv6[COL_ELEC] == 1) & (viv6[COL_SHG] == 1)
    ).astype(int)
    brecha = viv6.groupby(group_viv)['_acceso_completo'].agg(
        pct_brecha_servicios=lambda x: (1 - x.mean()) * 100
    ).reset_index()

    ind = env.merge(educ, on=group_per, how='outer')
    ind = ind.merge(hac, on=group_per, how='outer')
    ind = ind.merge(brecha, on=group_per, how='outer')

    # Normalización /max (0-1, igual que tarea_1) → luego *100 para Power BI
    dims = [c for c in ['pct_mayores65','pct_educ_baja','pct_hacinamiento','pct_brecha_servicios'] if c in ind.columns]
    for c in dims:
        mx = ind[c].max()
        ind[f'{c}_norm'] = (ind[c] / mx * 100).round(2) if mx > 0 else 0

    norm_cols = [f'{c}_norm' for c in dims]
    ind['indicador_desarrollo_compuesto'] = ind[norm_cols].mean(axis=1).round(2)

    q33 = ind['indicador_desarrollo_compuesto'].quantile(0.33)
    q66 = ind['indicador_desarrollo_compuesto'].quantile(0.66)
    ind['prioridad_politica_publica'] = ind['indicador_desarrollo_compuesto'].apply(
        lambda v: 'Alta prioridad' if v >= q66 else ('Media prioridad' if v >= q33 else 'Baja prioridad')
    )

    if top10_nombres:
        agregar_top10(ind, top10_nombres)
    ind.round(3).to_csv('tarea6_indicador_desarrollo.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ tarea6_indicador_desarrollo.csv ({len(ind)} comunas)")

    cols_show = ['nombre_provincia','nombre_comuna'] + dims + ['indicador_desarrollo_compuesto','prioridad_politica_publica']
    cols_show = [c for c in cols_show if c in ind.columns]
    print("\n  TOP 10 prioritarias (todas las comunas):")
    print(ind.nlargest(10,'indicador_desarrollo_compuesto')[cols_show].to_string(index=False))
    if top10_nombres:
        top10_ind = ind[ind['es_top10']=='Top 10']
        print("\n  TOP prioritarias (solo las 10 más pobladas — igual que tarea_1):")
        print(top10_ind.nlargest(10,'indicador_desarrollo_compuesto')[cols_show].to_string(index=False))


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

    top10 = calcular_top10(df_per)

    if solo_tarea4:
        print("\n--- Regenerando solo Tarea 4 ---")
        tarea4_educacion_actividad(df_per, top10)
    else:
        print("\n[2] Cargando vivienda...")
        df_viv = cargar_csv('vivienda_valpo.csv')
        if df_viv is None:
            print("\nERROR: falta vivienda_valpo.csv. Abortando.")
            input("\nPresiona Enter para cerrar...")
            return
        print("\n--- Procesando todo ---")
        tarea3_hacinamiento(df_viv, top10)
        tarea4_educacion_actividad(df_per, top10)
        tarea5_servicios_basicos(df_viv, top10)
        tarea6_indicador_desarrollo(df_per, df_viv, top10)

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
