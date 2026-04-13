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

disciplinas = ["Civil", "Elétrica", "Hidráulica", "Segurança contra Incêndio", "Mecânica (Climatização)", "Estrutura"]

sugestoes_inspecao = {
    "Civil": {
        "Problemas": ["Infiltração em laje/cobertura", "Fissuras em alvenaria", "Piso quebrado/solto", "Pintura descascando/com bolhas", "Porta/Janela com defeito"],
        "Soluções": ["Impermeabilização da superfície", "Tratamento de fissuras e reboco", "Substituição do revestimento", "Repintura com fundo preparador", "Manutenção ou troca da esquadria"]
    },
    "Elétrica": {
        "Problemas": ["Quadro elétrico sem identificação", "Fios expostos", "Tomada/Interruptor danificado", "Iluminação inoperante", "Disjuntor desarmando"],
        "Soluções": ["Identificação e diagrama do quadro", "Isolamento e embutimento de fiação", "Troca da tomada/interruptor", "Substituição de lâmpada/reator", "Revisão da carga e substituição do disjuntor"]
    },
    "Hidráulica": {
        "Problemas": ["Vazamento em tubulação", "Torneira pingando", "Descarga acoplada sem funcionar", "Ralo entupido", "Falta de pressão de água"],
        "Soluções": ["Localização e reparo da tubulação", "Troca do reparo da torneira", "Manutenção ou substituição do mecanismo da descarga", "Desentupimento e limpeza do ralo", "Limpeza do castelo d'água ou pressurização"]
    },
    "Outra": {
        "Problemas": ["Descreva o problema aqui..."],
        "Soluções": ["Sugira a solução aqui..."]
    }
}

# 4. BARRA LATERAL (SIDEBAR)
st.sidebar.title("⚙️ Painel de Controle")

# Seleção do Engenheiro
eng_sel = st.sidebar.selectbox("Engenheiro Responsável", list(mapa_engenheiros.keys()))

# --- AVATAR DINÂMICO ---
genero = mapa_engenheiros[eng_sel]
avatar_url = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png" if genero == "M" else "https://cdn-icons-png.flaticon.com/512/219/219969.png"
col_side1, col_side2, col_side3 = st.sidebar.columns([1,2,1])
with col_side2:
    st.image(avatar_url, use_container_width=True)
# -----------------------

campus_sel = st.sidebar.selectbox("Campus", mapa_campi[eng_sel])
st.sidebar.markdown("---")
choice = st.sidebar.radio("Navegação", ["Nova Inspeção", "Histórico de Registros"])

if st.sidebar.button("Sair do Sistema"):
    st.session_state['autenticado'] = False
    st.rerun()

# 5. CONEXÃO E INTERFACE PRINCIPAL
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("📋 Inspeção Predial - IFBA")
st.info(f"📍 **Campus:** {campus_sel} | 👷 **Responsável:** {eng_sel}")

if choice == "Nova Inspeção":
    with st.form("form_inspecao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            edificacao = st.text_input("Edificação / Bloco")
            disciplina = st.selectbox("Disciplina", disciplinas, index=0)
        with col2:
            data_ins = st.date_input("Data da Inspeção", datetime.now())
            ambiente = st.text_input("Ambiente / Sala")

        st.markdown("**🔍 Detalhes da Inspeção**")
        
        prob_sugerido = st.selectbox(f"Problema comum de '{disciplina}':", 
                                   sugestoes_inspecao.get(disciplina, sugestoes_inspecao["Outra"])["Problemas"])
        descricao = st.text_area("Descrição do Problema", value=prob_sugerido)

        sol_sugerida = st.selectbox(f"Sugestão de solução para '{disciplina}':", 
                                  sugestoes_inspecao.get(disciplina, sugestoes_inspecao["Outra"])["Soluções"])
        solucoes = st.text_area("Sugestão de Solução", value=sol_sugerida)
        
        foto = st.file_uploader("📸 Tirar Foto ou Escolher da Galeria", type=['jpg', 'jpeg', 'png'])

        if st.form_submit_button("✅ Salvar Registro"):
            foto_base64 = ""
            if foto:
                with st.spinner("Processando imagem..."):
                    img = Image.open(foto)
                    img.thumbnail((700, 700)) 
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG", quality=70)
                    foto_base64 = base64.b64encode(buffered.getvalue()).decode()

            novo_dado = pd.DataFrame([{
                "Data": data_ins.strftime("%d/%m/%Y"), "Campus": campus_sel, "Edificacao": edificacao,
                "Disciplina": disciplina, "Ambiente": ambiente, "Descricao": descricao, "Solucoes": solucoes,
                "Engenheiro": eng_sel, "Foto_Dados": foto_base64
            }])

            try:
                df_antigo = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
                df_final = pd.concat([df_antigo, novo_dado], ignore_index=True)
                conn.update(spreadsheet=URL_PLANILHA, data=df_final)
                st.success("✅ Tudo salvo com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

elif choice == "Histórico de Registros":
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        st.dataframe(df.drop(columns=['Foto_Dados'], errors='ignore'), use_container_width=True)
        if not df.empty:
            st.divider()
            id_linha = st.selectbox("Selecione o ID para ver detalhes:", df.index)
            reg = df.iloc[id_linha]
            st.markdown(f"### Detalhes do Registro #{id_linha}")
            if reg["Foto_Dados"]:
                st.image(base64.b64decode(reg["Foto_Dados"]), caption=f"Evidência - {reg['Ambiente']}", use_container_width=True)
            st.write(f"**Descrição:** {reg['Descricao']}")
            st.write(f"**Solução:** {reg['Solucoes']}")
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")

# --- RODAPÉ CENTRALIZADO NA PÁGINA ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #6d6d6d; font-size: 0.9em;">
        <strong>Desenvolvido por:</strong><br>
        Thiago Messias Carvalho Soares & Roger Ramos Santana<br>
        <span style="color: #2e7d32; font-weight: bold;">PRODIN - IFBA 2026</span>
    </div>
    """,
    unsafe_allow_html=True
)
