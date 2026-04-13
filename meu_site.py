import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from PIL import Image
import io
from fpdf import FPDF
import requests

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Sistema PRODIN - IFBA", layout="centered", page_icon="📋")

# 🔗 COLOQUE O LINK DA SUA PLANILHA AQUI
URL_PLANILHA = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"

# 2. SISTEMA DE ACESSO
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acesso Restrito - PRODIN")
    senha = st.text_input("Senha de acesso:", type="password")
    if st.button("Entrar"):
        if senha == "IFBA2026":
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# 3. MAPEAMENTO DE ENGENHEIROS E AVATARES (Boneco/Boneca Profissional)
mapa_engenheiros = {
    "Eng. Thiago": "M",
    "Eng. Roger": "M",
    "Eng. Laís": "F",
    "Eng. Larissa": "F",
    "Eng. Marcelo": "M",
    "Eng. Fenelon": "M"
}

# Banco de dados de patologias (Corrigido para evitar erro de aspas no "H")
sugestoes = {
    'Alvenaria': {
        'Problemas': ['Fissuras de retração térmica', 'Trincas em diagonal', 'Umidade ascendente', 'Eflorescência', 'Desaprumo', 'Fissuras em H (esmagamento)', 'Mofo/bolor'],
        'Soluções': ['Tela de poliéster e selante', 'Grampeamento com barras de aço', 'Impermeabilização polimérica', 'Limpeza química', 'Regularização de prumo']
    },
    'Estrutura': {
        'Problemas': ['Corrosão de armaduras', 'Ferragem exposta', 'Bicheiras (segregação)', 'Flechas excessivas', 'Carbonatação'],
        'Soluções': ['Passivação e recomposição', 'Tratamento anticorrosivo', 'Grauteamento estrutural', 'Reforço com fibra de carbono']
    },
    'Hidráulica': {
        'Problemas': ['Vazamento aparente', 'Baixa pressão', 'Registros pingando', 'Golpe de aríete'],
        'Soluções': ['Troca de conexões', 'Limpeza de filtros', 'Troca de vedantes', 'Válvula de alívio']
    },
    'Elétrica': {
        'Problemas': ['Fios expostos', 'Quadro sem identificação', 'Disjuntores desarmando', 'Aquecimento excessivo'],
        'Soluções': ['Isolamento em eletrodutos', 'Etiquetagem de circuitos', 'Redimensionamento de carga']
    }
}

lista_disciplinas = ["Escolha..."] + list(sugestoes.keys()) + ["Outras"]

# 4. BARRA LATERAL (SIDEBAR) COM AVATARES PROFISSIONAIS
with st.sidebar:
    st.title("⚙️ PRODIN - IFBA")
    
    eng_sel = st.selectbox("Engenheiro Responsável", list(mapa_engenheiros.keys()))
    
    # --- AVATAR DINÂMICO (HOMEM OU MULHER) ---
    genero = mapa_engenheiros[eng_sel]
    if genero == "M":
        icon_url = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png" # Avatar Masculino
    else:
        icon_url = "https://cdn-icons-png.flaticon.com/512/3135/3135768.png" # Avatar Feminino
        
    try:
        response = requests.get(icon_url)
        img_avatar = Image.open(io.BytesIO(response.content))
        st.image(img_avatar, width=120)
    except:
        st.write("👨‍💼" if genero == "M" else "👩‍💼")

    campus_sel = st.selectbox("Campus", ["Euclides da Cunha", "Feira de Santana", "Salvador", "Camaçari", "Vitória da Conquista", "Santo Amaro", "Simões Filho", "Eunápolis"])
    choice = st.sidebar.radio("Navegação", ["Nova Inspeção", "Histórico / Gerar PDF"])

# 5. CONEXÃO E FUNÇÕES
conn = st.connection("gsheets", type=GSheetsConnection)

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RELATÓRIO DE INSPEÇÃO PREDIAL - IFBA", ln=True, align='C')
    pdf.ln(10)
    for k, v in dados.items():
        if k != "Foto_Dados":
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(50, 7, f"{k}:", 0)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 7, f"{str(v)}", 0)
    return pdf.output(dest='S').encode('latin-1')

# --- TELA: NOVA INSPEÇÃO ---
if choice == "Nova Inspeção":
    st.header("📋 Registrar Inspeção Técnica")
    disciplina = st.selectbox("1. Escolha a Disciplina Técnica:", lista_disciplinas)
    
    with st.form("form_vFinal_Super", clear_on_submit=True):
        col_ed, col_dt = st.columns([2, 1])
        with col_ed:
            edificacao = st.selectbox("Edificação / Bloco", ["Pavilhão de Aulas", "Pavilhão Administrativo", "Refeitório", "Ginásio", "Muro", "Estacionamento", "Guarita", "Galpão Industrial", "Usina de Biodiesel", "Usina Solar"])
        with col_dt:
            data_ins = st.date_input("Data da Inspeção", datetime.now())

        col_amb, col_num = st.columns([2, 1])
        with col_amb:
            ambiente = st.selectbox("Ambiente / Sala", ["Laboratório", "Sala Administrativa", "Sala de Aulas", "Sanitário Masculino", "Sanitário Feminino", "Sanitário PCD", "Corredor", "Área Externa", "Outro"])
        with col_num:
            sala_num = st.text_input("Nº Sala", placeholder="Ex: 102")

        ambiente_final = f"{ambiente} - {sala_num}" if sala_num else ambiente
        
        desc_final = ""
        sol_final = ""

        if disciplina in sugestoes:
            st.divider()
            pat_sel = st.selectbox("Patologia Identificada:", sugestoes[disciplina]['Problemas'])
            desc_final = st.text_area("Detalhamento:", value=pat_sel)
            sol_sel = st.selectbox("Solução Sugerida:", sugestoes[disciplina]['Soluções'])
            sol_final = st.text_area("Encaminhamento:", value=sol_sel)
        
        foto = st.file_uploader("📸 Foto da Evidência", type=['jpg', 'jpeg', 'png'])

        if st.form_submit_button("✅ Salvar na Planilha"):
            if disciplina == "Escolha...":
                st.error("Selecione a disciplina!")
            else:
                foto_b64 = ""
                if foto:
                    img = Image.open(foto)
                    img.thumbnail((700, 700)) 
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=70)
                    foto_b64 = base64.b64encode(buf.getvalue()).decode()

                novo_reg = pd.DataFrame([{
                    "Data": data_ins.strftime("%d/%m/%Y"), "Campus": campus_sel, "Edificacao": edificacao, 
                    "Disciplina": disciplina, "Ambiente": ambiente_final, "Descricao": desc_final, 
                    "Solucoes": sol_final, "Engenheiro": eng_sel, "Foto_Dados": foto_b64
                }])

                try:
                    df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
                    df_f = pd.concat([df, novo_reg], ignore_index=True)
                    conn.update(spreadsheet=URL_PLANILHA, data=df_f)
                    st.success("✅ Registro salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

elif choice == "Histórico / Gerar PDF":
    st.header("📂 Histórico")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        st.dataframe(df.drop(columns=['Foto_Dados'], errors='ignore'))
        if not df.empty:
            id_sel = st.selectbox("Selecione o ID:", df.index)
            reg = df.iloc[id_sel]
            if reg["Foto_Dados"]:
                st.image(base64.b64decode(reg["Foto_Dados"]), width=300)
            pdf_bytes = gerar_pdf(reg.to_dict())
            st.download_button("📥 Baixar PDF", data=pdf_bytes, file_name=f"Inspecao_{id_sel}.pdf")
    except:
        st.error("Erro ao carregar histórico.")

# --- RODAPÉ ---
st.markdown("<br><hr><div style='text-align: center; color: gray;'><strong>Desenvolvido por:</strong><br>Thiago Messias Carvalho Soares & Roger Ramos Santana<br>PRODIN - IFBA 2026</div>", unsafe_allow_html=True)
