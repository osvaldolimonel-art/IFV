import streamlit as st
import math
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="STROM - Ingeniería FV", layout="wide")

# CSS para que se vea profesional como tu imagen
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; background-color: #00b050; color: white; font-weight: bold; border-radius: 10px; height: 3em; }
    .css-1r6slb0 { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE CÁLCULO ---
def calcular_todo(datos):
    # Voc Corregido por temperatura
    voc_corr = datos['voc'] * (1 + (datos['beta']/100.0) * (datos['tmin'] - 25))
    
    # Cálculos eléctricos
    potencia_total = (datos['vmp'] * datos['imp'] * datos['total_p']) / 1000.0
    i_dc = datos['isc'] * 1.56
    
    if datos['fases'] == "Trifásico":
        i_ac = (potencia_total * 1000) / (math.sqrt(3) * datos['vac'])
    else:
        i_ac = (potencia_total * 1000) / datos['vac']
        
    return voc_corr, potencia_total, i_dc, i_ac

# --- INTERFAZ TIPO DASHBOARD ---
with st.sidebar:
    st.header("STROM - Gestión")
    cliente = st.text_input("Nombre del Cliente", "Cliente Ejemplo")
    proyecto = st.text_input("Nombre del Proyecto", "Instalación Residencial")
    responsable = st.text_input("Responsable Técnico")
    cedula = st.text_input("Cédula Profesional")

st.title("⚡ FV PRO Engineering Tool")
st.info("Cálculos basados en la NOM-001-SEDE")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Datos de Placa (STC)")
    vmp = st.number_input("Vmp (V)", value=34.0)
    imp = st.number_input("Imp (A)", value=12.5)
    voc = st.number_input("Voc (V)", value=41.5)
    isc = st.number_input("Isc (A)", value=13.5)
    beta = st.number_input("Coeficiente Temperatura Voc (%)", value=-0.29)
    tmin = st.number_input("Temperatura Mínima Sitio (°C)", value=10)

with col2:
    st.subheader("🏗️ Configuración del Sistema")
    vmax_inv = st.number_input("Voltaje Máximo Inversor", value=1000)
    vac = st.selectbox("Voltaje AC", [220, 440, 480], index=0)
    fases = st.radio("Tipo de Sistema", ["Monofásico", "Trifásico"])
    
    n_mppt = st.number_input("Número de MPPTs", min_value=1, value=1)
    total_paneles = 0
    for i in range(n_mppt):
        p = st.number_input(f"Paneles en MPPT {i+1}", value=10, key=f"mppt_{i}")
        total_paneles += p

# --- PROCESAMIENTO ---
if st.button("CALCULAR Y GENERAR MEMORIA"):
    datos_dict = {
        'vmp': vmp, 'imp': imp, 'voc': voc, 'isc': isc, 
        'beta': beta, 'tmin': tmin, 'total_p': total_paneles,
        'vac': vac, 'fases': fases
    }
    
    v_corr, p_kw, idc, iac = calcular_todo(datos_dict)
    
    # Mostrar resultados rápidos
    c1, c2, c3 = st.columns(3)
    c1.metric("Potencia Instalada", f"{p_kw:.2f} kWp")
    c2.metric("Corriente DC (1.56)", f"{idc:.2f} A")
    c3.metric("Corriente AC", f"{iac:.2f} A")

    # Generar PDF en memoria (Buffer) para que funcione en la web
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"MEMORIA TÉCNICA: {proyecto}", styles['Title']))
    elements.append(Paragraph(f"Cliente: {cliente}", styles['Normal']))
    elements.append(Paragraph(f"Potencia: {p_kw:.2f} kW", styles['Normal']))
    elements.append(Paragraph(f"Corriente AC: {iac:.2f} A", styles['Normal']))
    
    doc.build(elements)
    
    st.download_button(
        label="📥 Descargar Memoria en PDF",
        data=buffer.getvalue(),
        file_name=f"Memoria_{cliente}.pdf",
        mime="application/pdf"
    )