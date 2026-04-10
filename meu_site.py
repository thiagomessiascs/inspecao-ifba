import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import io

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

# --- 2. FUNÇÃO GERADORA DE PDF POR CAMPUS ---
def gerar_pdf_campus(df_filtro, campus, eng_nome_completo):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Cabeçalho Centralizado
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, f"RELATÓRIO DE INSPEÇÃO PREDIAL - IFBA {campus.upper()}", ln=True, align='C')
    pdf.ln(5)
    
    # Loop por todas as patologias do Campus
    for i, row in df_filtro.iterrows():
        y_inicial = pdf.get_y()
        if y_inicial > 220: pdf.add_page(); y_inicial = pdf.get_y()
        
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(190, 8, f"Item {i+1}: {row['Edificacao']}", ln=True, fill=True)
        
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(30, 6, "Ambiente:", 0)
        pdf.set_font("Arial", '', 9)
        pdf.cell(80, 6, f"{row['Ambiente']}", ln=True)
        
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(110, 6, "Descrição da Patologia:", ln=True)
        pdf.set_font("Arial", '', 9)
        pdf.multi_cell(110, 5, f"{row['Descricao']}")
        
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(110, 6, "Soluções Sugeridas:", ln=True)
        pdf.set_font("Arial", '', 9)
        pdf.multi_cell(110, 5, f"{row['Solucoes']}")
        
        pdf.set_font("Arial", 'B', 9)
        cor = (211, 47, 47) if row['Status'] == "CRÍTICA" else (218, 165, 32)
        pdf.set_text_color(*cor)
        pdf.cell(110, 7, f"PRIORIDADE GUT: {row['Status']} (Score: {row['Score_GUT']})", ln=True)
        pdf.set_text_color(0, 0, 0)
        
        # Nota: As fotos no PDF só funcionam para uploads da sessão atual. 
        # Para relatórios históricos com fotos, seria necessário um servidor de arquivos (S3/Drive).
        
        pdf.ln(5)
        pdf.cell(190, 0, '', 'T', ln=True)
        pdf.ln(5)

    # Assinatura Final
    if pdf.get_y() > 240: pdf.add_page()
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "________________________________________________", ln=True, align='C')
    pdf.cell(0, 5, eng_nome_completo, ln=True, align='C')
    pdf.set_font("Arial", '', 9)
    pdf.cell(0, 5, "Engenheiro Civil - Equipe PRODIN IFBA", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. LOGIN ---
def verificar_senha():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if not st.session_state["autenticado"]:
        st.set_page_config(page_title="Login IFBA", page_icon="🔐")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔐 Login")
            senha = st.text_input("Senha:", type="password")
            if st.button("Entrar"):
                if senha == "IFBA2026":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else: st.error("Senha incorreta!")
        return False
    return True

# --- 4. APP ---
if verificar_senha():
    st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide")

    st.markdown("""
        <style>
        .profile-pic { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid #2e7d32; }
        </style>
    """, unsafe_allow_html=True)

    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df_base = conn.read(ttl="0")
    except:
        df_base = pd.DataFrame()

    with st.sidebar:
        st.header("👨‍🏫 Vistoriador")
        eng_nomes = list(EQUIPE.keys())
        eng_ativo = st.selectbox("Selecione seu nome:", eng_nomes)
        st.markdown(f'<div style="text-align: center;"><img src="{EQUIPE[eng_ativo]["foto"]}" class="profile-pic"></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        lista_campi = sorted(EQUIPE[eng_ativo]["campi"])
        campus_sel = st.selectbox("Campus da Vistoria:", lista_campi)
        
        if st.button("🚪 Sair"):
            st.session_state["autenticado"] = False
            st.rerun()

    st.markdown(f"## 🏗️ Sistema de Vistoria - {campus_sel}")
    
    # FORMULÁRIO (APENAS SALVA)
    with st.form("form_inspeção", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            edificacao = st.text_input("Edificação / Bloco:")
            disciplina = st.selectbox("Disciplina:", ["Alvenaria", "Estrutura", "Elétrica", "Hidráulica", "Pintura", "Cobertura", "Drenagem", "Incêndio"])
            ambiente = st.text_input("Ambiente:")
            descricao = st.text_area("Descrição:")
            solucoes = st.text_area("Sugestão de Solução:")
        with c2:
            st.write("**📸 Foto**")
            foto_vistoria = st.file_uploader("Tirar foto", type=["jpg", "png"])
            st.write("**📊 Matriz GUT**")
            g = st.select_slider("Gravidade", options=[1,2,3,4,5], value=3)
            u = st.select_slider("Urgência", options=[1,2,3,4,5], value=3)
            t = st.select_slider("Tendência", options=[1,2,3,4,5], value=3)
            score = g * u * t
            status = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
            st.info(f"Prioridade: {status}")

        if st.form_submit_button("💾 Salvar Patologia"):
            if edificacao and descricao:
                nova_data = {
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Engenheiro": eng_ativo,
                    "Campus": campus_sel,
                    "Edificacao": edificacao,
                    "Disciplina": disciplina,
                    "Ambiente": ambiente,
                    "Descricao": descricao,
                    "Solucoes": solucoes,
                    "Score_GUT": score,
                    "Status": status
                }
                df_updated = pd.concat([df_base, pd.DataFrame([nova_data])], ignore_index=True)
                conn.update(data=df_updated)
                st.success("Patologia registrada com sucesso! Próxima...")
                st.rerun()
            else:
                st.warning("Preencha os campos obrigatórios.")

    # SEÇÃO DO PDF (POR CAMPUS)
    st.markdown("---")
    st.subheader(f"📄 Fechamento de Relatório - {campus_sel}")
    
    if not df_base.empty:
        # Filtra todas as patologias já salvas desse campus
        df_campus = df_base[df_base['Campus'] == campus_sel].reset_index(drop=True)
        
        if not df_campus.empty:
            st.write(f"Existem **{len(df_campus)}** patologias cadastradas para este campus.")
            st.dataframe(df_campus[["Edificacao", "Ambiente", "Status"]], use_container_width=True)
            
            nome_completo_assinatura = EQUIPE[eng_ativo]["nome_completo"]
            
            if st.button(f"🏁 Gerar Relatório Completo {campus_sel}"):
                pdf_bytes = gerar_pdf_campus(df_campus, campus_sel, nome_completo_assinatura)
                st.download_button(
                    label="📥 Baixar PDF do Campus",
                    data=pdf_bytes,
                    file_name=f"Relatorio_Final_{campus_sel}.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("Nenhuma patologia cadastrada para este campus ainda.")

    st.caption(f"Logado como: {EQUIPE[eng_ativo]['nome_completo']} | IFBA 2026")
