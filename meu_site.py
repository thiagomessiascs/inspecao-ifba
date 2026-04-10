import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io
import requests
import base64

# --- 1. CONFIGURAÇÃO DA EQUIPE (PRODIN) ---
EQUIPE = {
    "Eng. Thiago": {
        "nome_completo": "Thiago Messias Carvalho Soares",
        "campi": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"],
        "foto": "https://github.com/thiagomessiascs/inspecao-ifba/blob/main/Thiago.jpg?raw=true" 
    },
    "Eng. Roger": {
        "nome_completo": "Roger Ramos Santana",
        "campi": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    },
    "Eng. Laís": {
        "nome_completo": "Lais Sampaio Machado",
        "campi": ["Barreiras", "Jaguaquara", "Jequié"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135823.png"
    },
    "Eng. Larissa": {
        "nome_completo": "Larissa da Silva Oliveira",
        "campi": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacã"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135823.png"
    },
    "Eng. Marcelo": {
        "nome_completo": "Marcelo Souza Almeida",
        "campi": ["Brumado", "Vitória da Conquista"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    },
    "Eng. Fenelon": {
        "nome_completo": "Fenelon Bispo Pereira de Souza",
        "campi": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    },
    "Eng. do Local": {
        "nome_completo": "Engenheiro Responsável do Local",
        "campi": ["Salvador", "Reitoria - Salvador", "Polo de Inovação", "Salinas da Margarida", "São Desidério"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    }
}

# --- 2. FUNÇÕES TÉCNICAS (UPLOAD E PDF) ---
def upload_para_nuvem(foto_arquivo):
    API_KEY = "6908985532588b58a18370126786a347"
    url = "https://api.imgbb.com/1/upload"
    try:
        encoded_image = base64.b64encode(foto_arquivo.read()).decode('utf-8')
        res = requests.post(url, data={"key": API_KEY, "image": encoded_image})
        return res.json()['data']['url'] if res.status_code == 200 else ""
    except: return ""

def gerar_pdf_final(df_filtro, campus, eng_nome):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, f"RELATÓRIO DE INSPEÇÃO PREDIAL - IFBA {campus.upper()}", ln=True, align='C')
    pdf.ln(5)
    
    for i, row in df_filtro.iterrows():
        y_pos = pdf.get_y()
        if y_pos > 200: pdf.add_page(); y_pos = pdf.get_y()
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(190, 8, f"Item {i+1}: {row['Edificacao']}", ln=True, fill=True)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(110, 6, f"Ambiente: {row['Ambiente']}", ln=True)
        pdf.set_font("Arial", '', 9)
        pdf.multi_cell(110, 5, f"Descrição: {row['Descricao']}")
        pdf.multi_cell(110, 5, f"Soluções: {row['Solucoes']}")
        if row['Link_Foto']:
            try:
                img_data = requests.get(row['Link_Foto']).content
                pdf.image(io.BytesIO(img_data), x=125, y=y_pos + 10, w=60)
            except: pass
        pdf.set_y(max(pdf.get_y(), y_pos + 60))
        pdf.ln(5)
        pdf.cell(190, 0, '', 'T', ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "________________________________________________", ln=True, align='C')
    pdf.cell(0, 5, eng_nome, ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. INTERFACE (LAYOUT CLÁSSICO) ---
st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide")

# Estilos do Layout Anterior
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stButton>button { width: 100%; background-color: #2e7d32; color: white; border-radius: 5px; }
    .profile-pic { width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 3px solid #2e7d32; margin-bottom: 10px; }
    .sidebar-content { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

if "autenticado" not in st.session_state: st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🔐 Login PRODIN")
        senha = st.text_input("Senha:", type="password")
        if st.button("Acessar Sistema"):
            if senha == "IFBA2026": st.session_state["autenticado"] = True; st.rerun()
            else: st.error("Senha incorreta")
else:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(ttl="0")

    # BARRA LATERAL (Vistoriador e Unidades)
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.subheader("🕵️ Vistoriador")
        eng_ativo = st.selectbox("Selecione o Engenheiro:", list(EQUIPE.keys()))
        st.markdown(f'<img src="{EQUIPE[eng_ativo]["foto"]}" class="profile-pic">', unsafe_allow_html=True)
        st.info(f"**{eng_ativo}**")
        
        st.markdown("---")
        st.subheader("🏢 Unidades PRODIN")
        campus_sel = st.selectbox("Selecione o Campus:", sorted(EQUIPE[eng_ativo]["campi"]))
        
        if st.button("Sair"): st.session_state["autenticado"] = False; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # BANNER CENTRAL
    col_img, col_txt = st.columns([1, 3])
    with col_img:
        st.image("https://github.com/thiagomessiascs/inspecao-ifba/blob/main/IFBA_Logo.png?raw=true", width=150)
    with col_txt:
        st.title("Sistema de Inspeção Predial - IFBA")
        st.write("Engenharia, Manutenção e Vistorias Técnicas")

    st.markdown(f"### 📝 Registro de Patologia: {campus_sel}")
    
    # FORMULÁRIO DE REGISTRO
    with st.form("form_vistoria", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            bloco = st.text_input("Edificação/Bloco:")
            local = st.text_input("Ambiente:")
            desc = st.text_area("Descrição da Patologia:")
            solu = st.text_area("Sugestão de Solução:")
        with c2:
            foto_cel = st.file_uploader("📸 Evidência Fotográfica (Câmera)", type=["jpg", "png", "jpeg"])
            st.write("**Avaliação GUT**")
            g = st.select_slider("Gravidade", options=[1,2,3,4,5], value=3)
            u = st.select_slider("Urgência", options=[1,2,3,4,5], value=3)
            t = st.select_slider("Tendência", options=[1,2,3,4,5], value=3)
            score = g * u * t
            status = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
            st.success(f"Prioridade Atual: {status} (Score: {score})")

        if st.form_submit_button("💾 Salvar Inspeção"):
            if bloco and desc:
                link_foto = upload_para_nuvem(foto_cel) if foto_cel else ""
                nova_linha = {
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Engenheiro": eng_ativo,
                    "Campus": campus_sel,
                    "Edificacao": bloco,
                    "Ambiente": local,
                    "Descricao": desc,
                    "Solucoes": solu,
                    "Link_Foto": link_foto,
                    "Score_GUT": score,
                    "Status": status
                }
                df_up = pd.concat([df_base, pd.DataFrame([nova_linha])], ignore_index=True)
                conn.update(data=df_up)
                st.balloons()
                st.success("Patologia registrada com sucesso!")
            else: st.error("Por favor, preencha a Edificação e a Descrição.")

    # ÁREA DE FECHAMENTO (PDF)
    st.markdown("---")
    df_campus = df_base[df_base['Campus'] == campus_sel]
    if not df_campus.empty:
        st.subheader(f"📋 Resumo do Campus: {campus_sel}")
        st.dataframe(df_campus[["Edificacao", "Ambiente", "Status"]], use_container_width=True)
        
        if st.button(f"🏁 Finalizar e Gerar PDF de {campus_sel}"):
            with st.spinner("Compilando relatório com fotos..."):
                pdf_data = gerar_pdf_final(df_campus, campus_sel, EQUIPE[eng_ativo]["nome_completo"])
                st.download_button("📥 Baixar Relatório Final", pdf_data, f"Relatorio_{campus_sel}.pdf", "application/pdf")
