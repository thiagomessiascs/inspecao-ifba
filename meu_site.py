import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from PIL import Image
import io

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Sistema de Inspeção IFBA", layout="centered", page_icon="📋")

# 🔗 COLOQUE O LINK DA SUA PLANILHA AQUI
URL_PLANILHA = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"

# 2. SISTEMA DE LOGIN
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acesso Restrito - IFBA")
    senha = st.text_input("Digite a senha de acesso:", type="password")
    if st.button("Entrar"):
        if senha == "IFBA2026":
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# 3. DICIONÁRIOS DE DADOS E AVATARES
mapa_engenheiros = {
    "Eng. Thiago": "M",
    "Eng. Roger": "M",
    "Eng. Laís": "F",
    "Eng. Larissa": "F",
    "Eng. Marcelo": "M",
    "Eng. Fenelon": "M",
    "Eng. do Local": "M"
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

sugestoes_inspecao = {
    "Civil": {
        "Problemas": ["Infiltração em laje/cobertura", "Fissuras em alvenaria", "Piso quebrado/solto", "Pintura descascando", "Esquadria danificada"],
        "Soluções": ["Impermeabilização", "Tratamento de fissuras e reboco", "Substituição de revestimento", "Repintura", "Manutenção/Troca de esquadria"]
    },
    "Elétrica": {
        "Problemas": ["Quadro sem identificação", "Fios expostos", "Tomada danificada", "Iluminação inoperante", "Disjuntor desarmando"],
        "Soluções": ["Identificação do quadro", "Isolamento de fiação", "Troca de acessório", "Substituição de lâmpadas", "Revisão de carga"]
    },
    "Hidráulica": {
        "Problemas": ["Vazamento visível", "Torneira pingando", "Descarga com defeito", "Ralo entupido", "Baixa pressão"],
        "Soluções": ["Reparo de tubulação", "Troca de reparo", "Manutenção de mecanismo", "Desentupimento", "Limpeza de caixa d'água"]
    }
}

# 4. BARRA LATERAL (SIDEBAR)
st.sidebar.title("⚙️ PRODIN")

# Seleção do Engenheiro
eng_sel = st.sidebar.selectbox("Engenheiro Responsável", list(mapa_engenheiros.keys()))

# --- AVATAR DINÂMICO ---
genero = mapa_engenheiros[eng_sel]
avatar = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png" if genero == "M" else "https://cdn-icons-png.flaticon.com/512/219/219969.png"
st.sidebar.image(avatar, width=100)
# -----------------------

campus_sel = st.sidebar.selectbox("Campus", mapa_campi[eng_sel])

st.sidebar.markdown("---")
choice = st.sidebar.radio("Navegação", ["Nova Inspeção", "Histórico"])

# --- RODAPÉ DOS DESENVOLVEDORES ---
st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; font-size: 0.8em; color: grey;'>
    <strong>Desenvolvido por:</strong><br>
    Thiago Messias Carvalho Soares<br>
    Roger Ramos Santana<br>
    <strong>PRODIN - IFBA 2026</strong>
</div>
""", unsafe_allow_html=True)

# 5. LÓGICA DO FORMULÁRIO
conn = st.connection("gsheets", type=GSheetsConnection)

if choice == "Nova Inspeção":
    st.header("📋 Nova Inspeção")
    with st.form("form_inspecao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            edificacao = st.text_input("Edificação / Bloco")
            disciplina = st.selectbox("Disciplina", ["Civil", "Elétrica", "Hidráulica", "Outros"])
        with col2:
            data_ins = st.date_input("Data", datetime.now())
            ambiente = st.text_input("Ambiente / Sala")

        # Sugestões Predefinidas
        sug_prob = sugestoes_inspecao.get(disciplina, {"Problemas": [""]})["Problemas"]
        sug_sol = sugestoes_inspecao.get(disciplina, {"Soluções": [""]})["Soluções"]
        
        prob_sel = st.selectbox("Selecione um problema comum:", sug_prob)
        descricao = st.text_area("Descrição Detalhada", value=prob_sel)
        
        sol_sel = st.selectbox("Selecione uma solução comum:", sug_sol)
        solucoes = st.text_area("Sugestão de Solução", value=sol_sel)
        
        foto = st.file_uploader("📸 Tirar Foto ou Galeria", type=['jpg', 'jpeg', 'png'])

        if st.form_submit_button("✅ Salvar"):
            foto_base64 = ""
            if foto:
                img = Image.open(foto)
                img.thumbnail((700, 700)) 
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=70)
                foto_base64 = base64.b64encode(buffered.getvalue()).decode()

            novo = pd.DataFrame([{
                "Data": data_ins.strftime("%d/%m/%Y"), "Campus": campus_sel, "Edificacao": edificacao,
                "Disciplina": disciplina, "Ambiente": ambiente, "Descricao": descricao, "Solucoes": solucoes,
                "Engenheiro": eng_sel, "Foto_Dados": foto_base64
            }])

            try:
                df_atual = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
                df_final = pd.concat([df_atual, novo], ignore_index=True)
                conn.update(spreadsheet=URL_PLANILHA, data=df_final)
                st.success("✅ Tudo salvo!")
            except Exception as e:
                st.error(f"Erro: {e}")

elif choice == "Histórico":
    st.header("📂 Histórico")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        st.dataframe(df.drop(columns=['Foto_Dados'], errors='ignore'))
        
        if not df.empty:
            id_sel = st.selectbox("Ver Foto do ID:", df.index)
            reg = df.iloc[id_sel]
            if reg["Foto_Dados"]:
                st.image(base64.b64decode(reg["Foto_Dados"]))
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
