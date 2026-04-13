import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from PIL import Image
import io
from fpdf import FPDF

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Sistema PRODIN - IFBA", layout="centered", page_icon="📋")

# 🔗 LINK DA SUA PLANILHA
URL_PLANILHA = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"

# 2. LOGIN
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acesso Restrito - PRODIN")
    senha = st.text_input("Senha:", type="password")
    if st.button("Entrar"):
        if senha == "IFBA2026":
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# 3. DICIONÁRIOS DE APOIO
mapa_engenheiros = {
    "Eng. Thiago": "M", "Eng. Roger": "M", "Eng. Laís": "F", 
    "Eng. Larissa": "F", "Eng. Marcelo": "M", "Eng. Fenelon": "M", "Eng. do Local": "M"
}

mapa_campi = {
    "Eng. Thiago": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"],
    "Eng. Roger": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"],
    "Eng. Laís": ["Barreiras", "Jaguaquara", "Jequié"],
    "Eng. Larissa": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacã"],
    "Eng. Marcelo": ["Brumado", "Vitória da Conquista"],
    "Eng. Fenelon": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"],
    "Eng. do Local": ["Salvador", "Reitoria", "Polo de Inovação", "Salinas da Margarida", "São Desidério"]
}

sugestoes = {
    "Civil": {
        "Problemas": ["Infiltração em laje", "Fissura em alvenaria", "Piso solto", "Pintura descascando", "Esquadria danificada"],
        "Soluções": ["Impermeabilização", "Tratamento de fissura", "Troca de revestimento", "Repintura", "Manutenção de esquadria"]
    },
    "Elétrica": {
        "Problemas": ["Quadro sem identificação", "Fios expostos", "Tomada danificada", "Iluminação inoperante", "Disjuntor desarmando"],
        "Soluções": ["Identificação de quadro", "Isolamento de fiação", "Troca de tomada", "Troca de lâmpadas", "Revisão de carga"]
    },
    "Hidráulica": {
        "Problemas": ["Vazamento de tubulação", "Torneira pingando", "Descarga com defeito", "Ralo entupido", "Baixa pressão"],
        "Soluções": ["Reparo de vazamento", "Troca de reparo", "Manutenção de descarga", "Desentupimento", "Limpeza de caixa d'água"]
    }
}

# 4. BARRA LATERAL
st.sidebar.title("⚙️ Painel de Controle")
eng_sel = st.sidebar.selectbox("Engenheiro Responsável", list(mapa_engenheiros.keys()))

# Avatar dinâmico
genero = mapa_engenheiros[eng_sel]
avatar = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png" if genero == "M" else "https://cdn-icons-png.flaticon.com/512/219/219969.png"
st.sidebar.image(avatar, width=100)

campus_sel = st.sidebar.selectbox("Campus", mapa_campi[eng_sel])
choice = st.sidebar.radio("Navegação", ["Nova Inspeção", "Histórico / PDF"])

# 5. CONEXÃO
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para Gerar PDF
def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RELATÓRIO DE INSPEÇÃO PREDIAL - IFBA", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for key, value in dados.items():
        if key != "Foto_Dados":
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, f"{key}:", 0)
            pdf.set_font("Arial", size=11)
            pdf.cell(100, 8, f"{value}", 0, 1)
    return pdf.output(dest='S').encode('latin-1')

# --- TELA 1: NOVA INSPEÇÃO ---
if choice == "Nova Inspeção":
    st.header("📋 Registrar Inspeção")
    with st.form("form_inspecao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            edificacao = st.text_input("Edificação / Bloco")
            disciplina = st.selectbox("Selecione a Disciplina", ["Selecione...", "Civil", "Elétrica", "Hidráulica", "Outros"])
        with col2:
            data_ins = st.date_input("Data", datetime.now())
            ambiente = st.text_input("Ambiente / Sala")

        # Lógica Condicional para Patologias
        descricao = ""
        solucoes = ""
        if disciplina != "Selecione...":
            st.markdown(f"---")
            prob_list = sugestoes.get(disciplina, {"Problemas": ["Outro"]})["Problemas"]
            sol_list = sugestoes.get(disciplina, {"Soluções": ["Outro"]})["Soluções"]
            
            prob_sel = st.selectbox("Patologia Identificada:", prob_list)
            descricao = st.text_area("Detalhamento da Patologia", value=prob_sel)
            
            sol_sel = st.selectbox("Solução Sugerida:", sol_list)
            solucoes = st.text_area("Detalhamento da Solução", value=sol_sel)

        foto = st.file_uploader("📸 Foto (Câmera ou Galeria)", type=['jpg', 'jpeg', 'png'])

        if st.form_submit_button("✅ Salvar na Planilha"):
            if disciplina == "Selecione...":
                st.error("Por favor, selecione uma disciplina.")
            else:
                foto_b64 = ""
                if foto:
                    img = Image.open(foto)
                    img.thumbnail((700, 700))
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=70)
                    foto_b64 = base64.b64encode(buf.getvalue()).decode()

                novo = pd.DataFrame([{
                    "Data": data_ins.strftime("%d/%m/%Y"), "Campus": campus_sel, "Edificacao": edificacao,
                    "Disciplina": disciplina, "Ambiente": ambiente, "Descricao": descricao, "Solucoes": solucoes,
                    "Engenheiro": eng_sel, "Foto_Dados": foto_b64
                }])

                try:
                    df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
                    df_f = pd.concat([df, novo], ignore_index=True)
                    conn.update(spreadsheet=URL_PLANILHA, data=df_f)
                    st.success("Inspeção salva com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# --- TELA 2: HISTÓRICO E PDF ---
elif choice == "Histórico / PDF":
    st.header("📂 Histórico de Inspeções")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        st.dataframe(df.drop(columns=['Foto_Dados'], errors='ignore'))
        
        if not df.empty:
            st.divider()
            id_sel = st.selectbox("Escolha um ID para ver detalhes e gerar PDF:", df.index)
            reg = df.iloc[id_sel]
            
            col_a, col_b = st.columns(2)
            with col_a:
                if reg["Foto_Dados"]:
                    st.image(base64.b64decode(reg["Foto_Dados"]), use_container_width=True)
            with col_b:
                st.write(f"**Campus:** {reg['Campus']}")
                st.write(f"**Descrição:** {reg['Descricao']}")
                st.write(f"**Solução:** {reg['Solucoes']}")
                
                # Botão PDF
                pdf_bytes = gerar_pdf(reg.to_dict())
                st.download_button(label="📥 Baixar PDF deste Registro", data=pdf_bytes, 
                                 file_name=f"Inspecao_{reg['Campus']}_{id_sel}.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")

# --- RODAPÉ CENTRALIZADO ---
st.markdown("<br><br><br><br>", unsafe_allow_html=True)
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: gray; font-size: 0.9em;">
        <strong>Desenvolvido por:</strong><br>
        Thiago Messias Carvalho Soares & Roger Ramos Santana<br>
        <span style="color: #2e7d32; font-weight: bold;">PRODIN - IFBA 2026</span>
    </div>
    """,
    unsafe_allow_html=True
)
