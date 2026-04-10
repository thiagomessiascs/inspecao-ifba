import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import io

# --- 1. CONFIGURAÇÃO DA EQUIPE (PRODIN) ---
# Nomes completos para assinatura e links das fotos de perfil
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

# --- 2. FUNÇÃO GERADORA DE PDF (FOTOS À DIREITA + ASSINATURA) ---
def gerar_pdf(dados, campus, eng_selecionado, foto_arquivo=None):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Cabeçalho do Relatório
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, f"RELATÓRIO DE INSPEÇÃO PREDIAL - IFBA {campus.upper()}", ln=True, align='C')
    pdf.ln(5)
    
    for i, row in dados.iterrows():
        y_inicial = pdf.get_y()
        
        # Título do Item com Fundo Cinza
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(190, 8, f"Item {i+1}: {row['Edificacao']}", ln=True, fill=True)
        
        # Coluna de Texto (Esquerda - Largura 110mm)
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
        
        # Status GUT com Cor
        pdf.set_font("Arial", 'B', 9)
        cor = (211, 47, 47) if row['Status'] == "CRÍTICA" else (218, 165, 32)
        pdf.set_text_color(*cor)
        pdf.cell(110, 7, f"PRIORIDADE GUT: {row['Status']} (Score: {row['Score_GUT']})", ln=True)
        pdf.set_text_color(0, 0, 0)
        
        # --- INSERÇÃO DA FOTO À DIREITA ---
        if foto_arquivo:
            try:
                img = Image.open(foto_arquivo)
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                img_temp = io.BytesIO()
                img.save(img_temp, format='JPEG')
                # Posiciona a foto: x=125, y=y_inicial+10, largura=60mm
                pdf.image(img_temp, x=125, y=y_inicial + 10, w=60)
            except:
                pass

        # Garante que o próximo item não encavale na foto
        pdf.set_y(max(pdf.get_y(), y_inicial + 55))
        pdf.ln(5)
        pdf.cell(190, 0, '', 'T', ln=True) # Linha divisória
        pdf.ln(5)

    # Assinatura do Engenheiro Responsável
    if pdf.get_y() > 240: pdf.add_page()
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "________________________________________________", ln=True, align='C')
    nome_full = EQUIPE[eng_selecionado]["nome_completo"]
    pdf.cell(0, 5, nome_full, ln=True, align='C')
    pdf.set_font("Arial", '', 9)
    pdf.cell(0, 5, "Engenheiro Civil - Equipe PRODIN IFBA", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. SISTEMA DE LOGIN ---
def verificar_senha():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if not st.session_state["autenticado"]:
        st.set_page_config(page_title="Acesso - Inspeção IFBA", page_icon="🔐")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔐 Login")
            senha = st.text_input("Senha de Acesso:", type="password")
            if st.button("Entrar"):
                if senha == "IFBA2026":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
        return False
    return True

# --- 4. APLICATIVO PRINCIPAL ---
if verificar_senha():
    st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide")

    # Estilos CSS (Perfil Circular e Cabeçalho)
    st.markdown("""
        <style>
        .profile-pic { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid #2e7d32; }
        .sidebar-content { display: flex; flex-direction: column; align-items: center; text-align: center; }
        </style>
    """, unsafe_allow_html=True)

    # Conexão com Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df_base = conn.read(ttl="0")
    except:
        df_base = pd.DataFrame()

    # Barra Lateral
    with st.sidebar:
        st.header("👨‍🏫 Vistoriador")
        eng_nomes = list(EQUIPE.keys())
        eng_ativo = st.selectbox("Selecione seu nome:", eng_nomes)
        
        st.markdown(f"""
            <div class="sidebar-content">
                <img src="{EQUIPE[eng_ativo]['foto']}" class="profile-pic">
                <p style="font-weight: bold; margin-top: 10px;">{eng_ativo}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        lista_campi = sorted(EQUIPE[eng_ativo]["campi"])
        campus_sel = st.selectbox("Campus da Vistoria:", lista_campi)
        
        if st.button("🚪 Sair"):
            st.session_state["autenticado"] = False
            st.rerun()

    # Formulário de Entrada
    st.markdown(f"## 🏗️ Sistema de Vistoria - {campus_sel}")
    
    with st.form("form_inspeção", clear_on_submit=True):
        col_form_1, col_form_2 = st.columns(2)
        
        with col_form_1:
            edificacao = st.text_input("Edificação / Bloco:")
            disciplina = st.selectbox("Disciplina:", ["Alvenaria", "Estrutura", "Elétrica", "Hidráulica", "Pintura", "Cobertura", "Drenagem", "Incêndio"])
            ambiente = st.text_input("Ambiente Específico:")
            descricao = st.text_area("Descrição da Ocorrência:")
            solucoes = st.text_area("Sugestão de Solução:")

        with col_form_2:
            st.write("**📸 Registro Fotográfico**")
            # Ao usar no celular, o botão abaixo aciona a câmera
            foto_vistoria = st.file_uploader("Tirar foto ou anexar", type=["jpg", "jpeg", "png"])
            if foto_vistoria:
                st.image(foto_vistoria, width=300)
            
            st.write("**📊 Matriz GUT (Gravidade, Urgência, Tendência)**")
            g = st.select_slider("Gravidade (O quão grave é?)", options=[1,2,3,4,5], value=3)
            u = st.select_slider("Urgência (Pode esperar?)", options=[1,2,3,4,5], value=3)
            t = st.select_slider("Tendência (Vai piorar rápido?)", options=[1,2,3,4,5], value=3)
            
            score = g * u * t
            status = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
            st.info(f"Prioridade Atual: **{status}** (Score: {score})")

        btn_salvar = st.form_submit_button("💾 Salvar Inspeção e Gerar PDF")

        if btn_salvar:
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
                
                # 1. Enviar para a Planilha
                df_updated = pd.concat([df_base, pd.DataFrame([nova_data])], ignore_index=True)
                conn.update(data=df_updated)
                
                # 2. Gerar PDF apenas deste item para download imediato
                pdf_output = gerar_pdf(pd.DataFrame([nova_data]), campus_sel, eng_ativo, foto_vistoria)
                
                st.success("✅ Dados salvos com sucesso!")
                st.download_button(
                    label="📄 Baixar PDF desta Inspeção",
                    data=pdf_output,
                    file_name=f"Vistoria_{campus_sel}_{edificacao}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Por favor, preencha a Edificação e a Descrição.")

    # Rodapé Profissional
    st.markdown("---")
    st.caption(f"Logado como: {EQUIPE[eng_ativo]['nome_completo']} | PRODIN - IFBA 2026")
