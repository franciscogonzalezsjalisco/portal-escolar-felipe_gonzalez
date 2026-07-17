import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
from datetime import datetime
import pytz
from urllib.parse import quote
import time

# 1. CONFIGURACIÓN E IDENTIDAD
st.set_page_config(page_title="Portal Escolar 6°B Urb. 690", layout="centered")

NOMBRE_MAESTRO = "Profr. Francisco González"

# MEJORA 1: Seguridad de la contraseña usando st.secrets (con un valor por defecto si no está configurado)
# Para desarrollo local, crea un archivo en .streamlit/secrets.toml con: PASS_MAESTRO = "TuContraseñaSegura"
PASS_MAESTRO = st.secrets.get("PASS_MAESTRO", "6B2026") 

URL_ESCUDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/ESCUDO%20690%20(1).png"
URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"
URL_LOG_SCRIPT = "https://script.google.com/macros/s/AKfycbwNGbSsky_dCyzvhf0WGfWj0mJMxR74Jrz2jmpIkJYLUDsH07cTCQjgbKO2E-TlaN_G/exec"

if 'pantalla' not in st.session_state: st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state: st.session_state.semana_activa = None
if 'ID_USUARIO' not in st.session_state: st.session_state.ID_USUARIO = ""
if 'alumno_datos' not in st.session_state: st.session_state.alumno_datos = None

# 2. --- ESTILOS DE DISEÑO ---
st.markdown(f"""
    <style>
    .stApp {{ 
        background-color: white !important; 
        background: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), url("{URL_FONDO}"); 
        background-size: cover; 
    }}
    
    h1, h2, h3, h4, p, label {{ color: #1D3557 !important; font-family: 'Segoe UI', sans-serif; }}

    .banner-maestro {{ 
        text-align: center; 
        background-color: #1D3557 !important; 
        padding: 20px; 
        border-radius: 15px; 
        margin-bottom: 25px; 
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }}
    
    .banner-maestro h2, .banner-maestro h3, .banner-maestro p {{
        color: #FFFFFF !important;
        margin: 5px 0px !important;
    }}

    div[data-baseweb="select"] {{
        border: 2px solid #1D3557 !important;
        border-radius: 12px !important;
    }}
    
    div.stButton > button {{ 
        background-color: white !important; 
        color: #1D3557 !important; 
        border: 2px solid #1D3557 !important; 
        border-radius: 12px !important; 
        font-weight: bold; 
    }}

    .footer {{
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(255, 255, 255, 0.9);
        color: #1D3557;
        text-align: center;
        padding: 5px;
        font-size: 12px;
        font-weight: bold;
        border-top: 1px solid #1D3557;
        z-index: 999;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. --- ENCABEZADO PRINCIPAL ---
st.markdown(f"""
    <div style='text-align: center;'>
        <img src="{URL_ESCUDO}" width="120" style="margin-bottom: 10px;">
        <h2 style='margin-top:0;'>URBANA 690</h2>
        <h4 style='color: #457B9D !important;'>6° Grado Grupo B</h4>
    </div>
    """, unsafe_allow_html=True)
st.markdown("---")

# 4. FUNCIONES
def registrar_en_bitacora(matricula, nombre, semana, accion):
    try:
        ts = datetime.now(pytz.timezone('America/Mexico_City')).strftime("%d/%m/%Y %H:%M:%S")
        params = {"fecha": ts, "matricula": str(matricula), "nombre": str(nombre), "semana": str(semana), "accion": str(accion)}
        headers = {"User-Agent": "Mozilla/5.0"}
        requests.get(URL_LOG_SCRIPT, params=params, headers=headers, timeout=10)
        st.toast(f"Registro: {accion}", icon="✅")
    except Exception as e:
        # MEJORA 2: Manejo de errores no silencioso
        print(f"Error al registrar en bitácora: {e}")

def procesar_valor(val):
    v_str = str(val).strip().upper()
    if v_str in ['NAN', '', '0', '0.0', 'FALSE', 'FALSO']: return "❌ Pendiente"
    if v_str in ['1', '1.0', 'TRUE', 'VERDADERO']: return "✅ Completado"
    return str(val)

# Función de apoyo para evitar errores de codificación en FPDF clásico (si no usas fpdf2)
def sanear_texto(texto):
    return str(texto).encode('latin-1', 'replace').decode('latin-1')

def crear_hoja_alumno_pdf(pdf, datos, semana, es_grupal=False):
    pdf.add_page()
    
    # MEJORA 4: (Opcional) Si subes un archivo Arial.ttf a tu repo, descomenta las siguientes dos líneas para soporte total de acentos/ñ
    # pdf.add_font('ArialUnicode', '', 'Arial.ttf', uni=True)
    # pdf.set_font("ArialUnicode", "", 14)
    # Mientras tanto, usaremos sanear_texto() para evitar que la aplicación se caiga con caracteres especiales.
    
    nombre_full = f"{datos.get('NOMBRE', '')} {datos.get('PATERNO', '')} {datos.get('MATERNO', '')}".strip()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(29, 53, 87)
    pdf.cell(0, 10, sanear_texto(f"REPORTE ESCOLAR: {nombre_full}"), ln=True, align="C")
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, sanear_texto(f"Semana: {semana} | Maestro: {NOMBRE_MAESTRO}"), ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_fill_color(29, 53, 87); pdf.set_text_color(255, 255, 255)
    pdf.cell(140, 8, " ACTIVIDAD", border=1, fill=True)
    pdf.cell(50, 8, " ESTADO", border=1, fill=True, ln=True)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", "", 9)
    omitir = ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']
    
    for k, v in datos.items():
        if k.upper() not in omitir and not str(k).startswith('Unnamed'):
            actividad_str = sanear_texto(f" {str(k)[:75]}")
            estado_str = sanear_texto(f" {procesar_valor(v).replace('❌ ','').replace('✅ ','')}")
            pdf.cell(140, 7, actividad_str, border=1)
            pdf.cell(50, 7, estado_str, border=1, ln=True)
            
    if not es_grupal:
        pdf.ln(10); pdf.set_font("Helvetica", "I", 8); pdf.set_text_color(100, 100, 100)
        ts = datetime.now(pytz.timezone('America/Mexico_City')).strftime("%d/%m/%Y %H:%M:%S")
        pdf.multi_cell(0, 5, sanear_texto(f"Descarga oficial: {ts} hrs.\nMatrícula: {datos.get('MATRICULA','')}"), align='C')

@st.cache_data(ttl=60)
def obtener_nombres_hojas(sid):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=xlsx"
        xls = pd.ExcelFile(url, engine='openpyxl')
        return xls.sheet_names
    except Exception as e: 
        print(f"Error al obtener hojas: {e}")
        return ["Semana 1"]

# MEJORA 3: Caché para evitar saturar Google Sheets y hacer la app mucho más rápida (guarda los datos por 5 minutos)
@st.cache_data(ttl=300)
def cargar_datos(nombre_hoja):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}&t={int(time.time())}"
    return pd.read_csv(url)

# --- FLUJO DE PANTALLAS ---
listado_hojas = obtener_nombres_hojas(SHEET_ID)

if st.session_state.pantalla == 'inicio':
    st.markdown("<h4 style='text-align: center;'>Selecciona la semana</h4>", unsafe_allow_html=True)
    for i in range(0, len(listado_hojas), 2):
        cols = st.columns(2)
        for j in range(2):
            idx = i + j
            if idx < len(listado_hojas):
                if cols[j].button(listado_hojas[idx], key=f"btn_{idx}"):
                    st.session_state.semana_activa = listado_hojas[idx]
                    st.session_state.pantalla = 'matricula'; st.rerun()
    st.markdown("---")
    
  # --- ACCESO MAESTRO ---
    with st.expander("🔐 Acceso Maestro"):
        pw = st.text_input("Contraseña:", type="password")
        if pw == PASS_MAESTRO:
            
            # --- NUEVA LÓGICA: Extraer la lista de alumnos automáticamente ---
            # Usamos la primera hoja disponible para construir un diccionario de {Nombre: Matrícula}
            df_alumnos = cargar_datos(listado_hojas[0])
            # Aseguramos que los nombres de las columnas estén en mayúsculas para no fallar
            df_alumnos.columns = [str(c).strip().upper() for c in df_alumnos.columns] 
            
            diccionario_alumnos = {}
            col_m = [c for c in df_alumnos.columns if "MATRICULA" in c]
            
            if col_m:
                col_matricula = col_m[0]
                for _, row in df_alumnos.iterrows():
                    mat = str(row[col_matricula]).replace('.0', '').strip()
                    # Verificamos que sea una matrícula válida
                    if mat and mat != 'NAN':
                        pat = str(row.get('PATERNO', '')).strip()
                        mat_ape = str(row.get('MATERNO', '')).strip()
                        nom = str(row.get('NOMBRE', '')).strip()
                        
                        # Limpiamos textos vacíos o nulos
                        pat = "" if pat == "NAN" else pat
                        mat_ape = "" if mat_ape == "NAN" else mat_ape
                        nom = "" if nom == "NAN" else nom
                        
                        # Armamos el nombre empezando por apellidos
                        nombre_completo = f"{pat} {mat_ape} {nom}".strip()
                        if nombre_completo:
                            diccionario_alumnos[nombre_completo] = mat
            
            # Ordenamos los nombres alfabéticamente
            nombres_ordenados = sorted(diccionario_alumnos.keys())
            
            # Creamos dos pestañas para organizar las descargas
            tab1, tab2 = st.tabs(["👥 Reporte Grupal", "👤 Reporte Histórico / Especializado"])
            
            # PESTAÑA 1: Todo el grupo, una semana
            with tab1:
                sem_m = st.selectbox("Semana para reporte grupal:", listado_hojas)
                if st.button("🚀 GENERAR PDF GRUPAL"):
                    with st.spinner("Generando..."):
                        df_m = cargar_datos(sem_m)
                        pdf_m = FPDF()
                        for _, f in df_m.iterrows(): 
                            crear_hoja_alumno_pdf(pdf_m, f.to_dict(), sem_m, es_grupal=True)
                        pdf_bytes = bytes(pdf_m.output())
                        st.download_button(label=f"📥 Descargar {sem_m}", data=pdf_bytes, file_name=f"Grupo_6B_{sem_m}.pdf", mime="application/pdf")
                        registrar_en_bitacora("MAESTRO", NOMBRE_MAESTRO, sem_m, "Descarga Masiva")
            
            # PESTAÑA 2: Un alumno, selección de semanas específicas
            with tab2:
                
                # NUEVO: Menú desplegable inteligente
                if nombres_ordenados:
                    alumno_seleccionado = st.selectbox("🧑‍🎓 Selecciona al alumno:", nombres_ordenados)
                    mat_hist = diccionario_alumnos[alumno_seleccionado] # Sacamos la matrícula invisiblemente
                else:
                    st.warning("No se pudo cargar la lista de alumnos automáticamente.")
                    mat_hist = st.text_input("Ingresa la matrícula del alumno a buscar:")
                
                st.markdown("**📅 Selecciona las semanas a incluir en el reporte:**")
                semanas_seleccionadas = st.multiselect(
                    "Semanas disponibles:", 
                    options=listado_hojas, 
                    default=listado_hojas 
                )
                
                if st.button("🚀 GENERAR REPORTE ESPECIALIZADO"):
                    if mat_hist.strip() == "":
                        st.warning("⚠️ Por favor, asegúrate de que haya un alumno seleccionado.")
                    elif len(semanas_seleccionadas) == 0:
                        st.warning("⚠️ Por favor, selecciona al menos una semana.")
                    else:
                        with st.spinner("Buscando y generando reporte..."):
                            pdf_hist = FPDF()
                            hubo_datos = False
                            nombre_alumno_hist = ""
                            
                            for sem in semanas_seleccionadas:
                                df_h = cargar_datos(sem)
                                df_h.columns = [str(c).strip() for c in df_h.columns]
                                col_m_hist = [c for c in df_h.columns if "MATRICULA" in c.upper()]
                                
                                if col_m_hist:
                                    df_h['BUSCAR'] = df_h[col_m_hist[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
                                    fila = df_h[df_h['BUSCAR'] == mat_hist.strip()]
                                    
                                    if not fila.empty:
                                        hubo_datos = True
                                        datos_al = fila.iloc[0].to_dict()
                                        if nombre_alumno_hist == "":
                                            nombre_alumno_hist = f"{datos_al.get('PATERNO', '')}_{datos_al.get('NOMBRE', '')}".strip()
                                        crear_hoja_alumno_pdf(pdf_hist, datos_al, sem, es_grupal=False)
                            
                            if hubo_datos:
                                pdf_bytes_hist = bytes(pdf_hist.output())
                                st.download_button(
                                    label=f"📥 Descargar Reporte de {nombre_alumno_hist}", 
                                    data=pdf_bytes_hist, 
                                    file_name=f"Reporte_Especializado_{nombre_alumno_hist}.pdf", 
                                    mime="application/pdf"
                                )
                                registrar_en_bitacora("MAESTRO", NOMBRE_MAESTRO, "ESPECIALIZADO", f"Descarga {mat_hist}")
                            else:
                                st.error("❌ Alumno no encontrado en las semanas seleccionadas.")

elif st.session_state.pantalla == 'matricula':
    st.markdown(f"<h4 style='text-align: center;'>📍 {st.session_state.semana_activa}</h4>", unsafe_allow_html=True)
    mat_in = st.text_input("Matrícula:", value=st.session_state.get('ID_USUARIO', ""))
    if st.button("🔍 VER REPORTE"):
        st.session_state.ID_USUARIO = mat_in.strip()
        df = cargar_datos(st.session_state.semana_activa)
        df.columns = [str(c).strip() for c in df.columns]
        col_m = [c for c in df.columns if "MATRICULA" in c.upper()]
        if col_m:
            df['BUSCAR'] = df[col_m[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
            fila = df[df['BUSCAR'] == st.session_state.ID_USUARIO]
            if not fila.empty:
                st.session_state.alumno_datos = fila.iloc[0].to_dict()
                registrar_en_bitacora(st.session_state.ID_USUARIO, st.session_state.alumno_datos.get('NOMBRE',''), st.session_state.semana_activa, "Ingreso")
                st.session_state.pantalla = 'resultados'; st.rerun()
            else: st.error("❌ Matrícula no encontrada")
    if st.button("⬅️ VOLVER"): st.session_state.pantalla = 'inicio'; st.rerun()

elif st.session_state.pantalla == 'resultados':
    datos = st.session_state.alumno_datos
    nombre_c = f"{datos.get('NOMBRE', '')} {datos.get('PATERNO', '')}"
    st.markdown(f'<div class="banner-maestro"><h3>Bienvenido(a):</h3><h2>{nombre_c}</h2><p>Matrícula: {st.session_state.ID_USUARIO}</p></div>', unsafe_allow_html=True)
    
    idx_s = listado_hojas.index(st.session_state.semana_activa)
    nueva_s = st.selectbox("📅 **Ver otra semana:**", listado_hojas, index=idx_s)
    if nueva_s != st.session_state.semana_activa:
        st.session_state.semana_activa = nueva_s
        df_n = cargar_datos(nueva_s); df_n.columns = [str(c).strip() for c in df_n.columns]
        col_m = [c for c in df_n.columns if "MATRICULA" in c.upper()]
        df_n['BUSCAR'] = df_n[col_m[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
        fila = df_n[df_n['BUSCAR'] == st.session_state.ID_USUARIO]
        if not fila.empty:
            st.session_state.alumno_datos = fila.iloc[0].to_dict()
            registrar_en_bitacora(st.session_state.ID_USUARIO, nombre_c, nueva_s, "Cambio Semana")
            st.rerun()

    res_f = {k: v for k, v in datos.items() if k.upper() not in ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']}
    entregas = sum(1 for v in res_f.values() if str(v).strip() not in ['0', '0.0', 'nan', '', 'False'])
    porc = int((entregas / len(res_f)) * 100) if len(res_f) > 0 else 0
    st.markdown(f'**Cumplimiento: {porc}%**')
    st.markdown(f'<div style="width:100%; background:#e0e0e0; border-radius:10px; height:18px;"><div style="width:{porc}%; background:#1D3557; height:18px; border-radius:10px;"></div></div>', unsafe_allow_html=True)
    
    df_res = pd.DataFrame(res_f.items(), columns=["Actividad", "Estado"])
    df_res["Estado"] = df_res["Estado"].apply(procesar_valor)
    filas = "".join([f'<tr><td style="border:1px solid #ddd; padding:8px;">{r["Actividad"]}</td><td style="border:1px solid #ddd; padding:8px; font-weight:bold;">{r["Estado"]}</td></tr>' for _, r in df_res.iterrows()])
    st.markdown(f'<div style="background:white; padding:10px; border-radius:10px; border:1px solid #1D3557;"><table style="width:100%; border-collapse:collapse; color:black;"><tr style="background:#eee;"><th>Actividad</th><th>Estado</th></tr>{filas}</table></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        pdf_ind = FPDF()
        crear_hoja_alumno_pdf(pdf_ind, datos, st.session_state.semana_activa)
        st.download_button(f"📥 PDF", data=bytes(pdf_ind.output()), file_name=f"Reporte_{datos.get('PATERNO','')}.pdf")
    with c2:
        if st.button("👥 SALIR"): st.session_state.pantalla = 'inicio'; st.rerun()

# 5. PIE DE PÁGINA FIJO
st.markdown(f'<div class="footer">{NOMBRE_MAESTRO}</div>', unsafe_allow_html=True)
