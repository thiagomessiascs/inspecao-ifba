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

# 3. DICIONÁRIOS DE DADOS PREDEFINIDOS
# Mapeamento de Engenheiros e Gênero (M: Masculino, F: Feminino)
mapa_engenheiros = {
    "Eng. Thiago": "M",
    "Eng. Roger": "M",
    "Eng. Laís": "F",
    "Eng. Larissa": "F",
    "Eng. Marcelo": "M",
    "Eng. Fenelon": "M",
    "Eng. do Local": "M"
}

# Mapeamento de Engenheiros e seus respectivos Campi
mapa_campi = {
    "Eng. Thiago": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"],
    "Eng. Roger": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"],
    "Eng. Laís": ["Barreiras", "Jaguaquara", "Jequié"],
    "Eng. Larissa": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacã"],
    "Eng. Marcelo": ["Brumado", "Vitória da Conquista"],
    "Eng. Fenelon": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"],
    "Eng. do Local": ["Salvador", "Reitoria", "Polo de Inovação", "Salinas da Margarida", "São Desidério"]
}

# Disciplinas predefinidas
disciplinas = ["Civil", "Elétrica", "Hidráulica", "Segurança contra Incêndio", "Mecânica (Climatização)", "Estrutura"]

# Problemas (Patologias) e Soluções Sugeridas
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
    # Adicionar mais categorias conforme necessidade
    "Outra": {
        "Problemas": ["Descreva o problema aqui..."],
        "Soluções": ["Sugira a solução aqui..."]
    }
}

# 4. BARRA LATERAL (SIDEBAR)
st.sidebar.title("⚙️ Painel de Controle")

# Seleção do Engenheiro
eng_selecionado = st.sidebar.selectbox("Engenheiro Responsável", list(mapa_engenheiros.keys()))

# --- NOVIDADE 1: AVATAR DO ENGENHEIRO ---
genero = mapa_engenheiros[eng_selecionado]
if genero == "M":
    avatar_url = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png" # Ícone de bonequinho engenheiro
else:
    avatar_url = "https://cdn-icons-png.flaticon.com/512/219/219969.png" # Ícone de bonequinha engenheira

col1, col2, col3 = st.sidebar.columns([1,2,1])
with col2:
    st.image(avatar_url, use_column_width=True)
# ---------------------------------------

# Seleção do Campus (Filtrado pelo Engenheiro)
campus_selecionado = st.sidebar.selectbox("Campus", mapa_campi[eng_selecionado])

st.sidebar.markdown("---")
choice = st.sidebar.radio("Navegação", ["Nova Inspeção", "Histórico de Registros"])

if st.sidebar.button("Sair"):
    st.session_state['autenticado'] = False
    st.rerun()

# 5. CONEXÃO E INTERFACE PRINCIPAL
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("📋 Inspeção Predial - IFBA")
st.subheader(f"📍 {campus_selecionado}")

if choice == "Nova Inspeção":
    with st.form("form_inspecao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            edificacao = st.text_input("Edificação / Bloco")
            
            # --- NOVIDADE 2: SELEÇÃO DE DISCIPLINA PREDEFINIDA ---
            disciplina = st.selectbox("Disciplina", disciplinas, index=0)
            # ---------------------------------------------------
            
        with col2:
            data_ins = st.date_input("Data da Inspeção", datetime.now())
            ambiente = st.text_input("Ambiente / Sala")

        # --- NOVIDADE 3: PATOLOGIAS E SOLUÇÕES PREDEFINIDAS ---
        # Sugestões baseadas na disciplina selecionada
        st.markdown("**🔍 Detalhes da Inspeção**")
        
        # Seleção de Problema Predefinido (Selectbox com busca)
        problema_sugerido = st.selectbox(
            f"Escolha um problema comum de '{disciplina}':",
            sugestoes_inspecao.get(disciplina, sugestoes_inspecao["Outra"])["Problemas"],
            help="Ou selecione 'Outro' para digitar manualmente abaixo."
        )
        
        # Campo de texto opcional para detalhar ou usar caso não esteja na lista
        descricao = st.text_area("Descrição do Problema", value=problema_sugerido, help="Você pode editar o texto sugerido.")

        # Seleção de Solução Predefinida (Selectbox com busca)
        solucao_sugerida = st.selectbox(
            f"Sugestão de solução para '{disciplina}':",
            sugestoes_inspecao.get(disciplina, sugestoes_inspecao["Outra"])["Soluções"],
            help="Ou selecione 'Outro' para digitar manualmente abaixo."
        )
        
        # Campo de texto opcional para detalhar ou usar caso não esteja na lista
        solucoes = st.text_area("Sugestão de Solução / Encaminhamento", value=solucao_sugerida, help="Você pode editar o texto sugerido.")
        # -----------------------------------------------------
        
        # Lógica de Captura: No celular permite tirar foto na hora ou escolher da galeria
        foto = st.file_uploader("📸 Tirar Foto ou Escolher da Galeria", type=['jpg', 'jpeg', 'png'])

        if st.form_submit_button("✅ Salvar Registro"):
            foto_base64 = ""
            
            if foto:
                with st.spinner("Processando imagem..."):
                    img = Image.open(foto)
                    # Redimensiona mantendo a proporção para não estourar a planilha
                    img.thumbnail((700, 700)) 
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG", quality=70)
                    foto_base64 = base64.b64encode(buffered.getvalue()).decode()

            # Preparação dos dados para a Planilha
            novo_dado = pd.DataFrame([{
                "Data": data_ins.strftime("%d/%m/%Y"),
                "Campus": campus_selecionado,
                "Edificacao": edificacao,
                "Disciplina": disciplina,
                "Ambiente": ambiente,
                "Descricao": descricao,
                "Solucoes": solucoes,
                "Engenheiro": eng_selecionado,
                "Foto_Dados": foto_base64 # A foto vira texto e vai direto para a planilha
            }])

            try:
                # Lê a planilha atual
                df_antigo = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
                # Adiciona o novo registro
                df_final = pd.concat([df_antigo, novo_dado], ignore_index=True)
                # Atualiza o Google Sheets
                conn.update(spreadsheet=URL_PLANILHA, data=df_final)
                st.success("✅ Registro enviado com sucesso! A foto está salva no seu celular e no banco de dados.")
            except Exception as e:
                st.error(f"Erro ao salvar na planilha: {e}")

elif choice == "Histórico de Registros":
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        # Mostramos a tabela sem a coluna gigante de texto da foto
        st.dataframe(df.drop(columns=['Foto_Dados'], errors='ignore'), use_container_width=True)
        
        if not df.empty:
            st.divider()
            id_linha = st.selectbox("Selecione o ID para ver os detalhes e a foto:", df.index)
            reg = df.iloc[id_linha]
            
            st.markdown(f"### Detalhes do Registro #{id_linha}")
            st.write(f"**Engenheiro:** {reg['Engenheiro']}")
            st.write(f"**Descrição:** {reg['Descricao']}")
            st.write(f"**Sugestão de Solução:** {reg['Solucoes']}")
            
            # Converte o Base64 de volta para imagem na tela
            if "Foto_Dados" in reg and reg["Foto_Dados"]:
                img_bytes = base64.b64decode(reg["Foto_Dados"])
                st.image(img_bytes, caption=f"Evidência - {reg['Ambiente']}", use_column_width=True)
            else:
                st.info("Este registro não possui foto anexa.")
    except Exception as e:
        st.error(f"Erro ao carregar o histórico: {e}")

# RODAPÉ DE CRÉDITOS
st.sidebar.markdown("---")
st.sidebar.info(f"""
**Desenvolvido por:**
* Thiago Messias Carvalho Soares
* Roger Ramos Santana

*PRODIN - IFBA 2026*
""")
