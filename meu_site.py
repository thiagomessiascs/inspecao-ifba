import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from PIL import Image
import io

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Sistema de Inspeção IFBA", layout="centered", page_icon="📋")

# 🔗 LINK DA SUA PLANILHA (O mesmo que você usa no navegador)
URL_PLANILHA = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"

# 2. SISTEMA DE ACESSO
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acesso Restrito - PRODIN")
    senha = st.text_input("Digite a senha de acesso:", type="password")
    if st.button("Entrar"):
        if senha == "IFBA2026":
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# 3. MAPEAMENTO DE RESPONSABILIDADES (CONFORME BANNER PRODIN)
mapa_prodin = {
    "Eng. Thiago": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"],
    "Eng. Roger": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"],
    "Eng. Laís": ["Barreiras", "Jaguaquara", "Jequié"],
    "Eng. Larissa": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacã"],
    "Eng. Marcelo": ["Brumado", "Vitória da Conquista"],
    "Eng. Fenelon": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"],
    "Eng. do Local": ["Salvador", "Reitoria", "Polo de Inovação", "Salinas da Margarida", "São Desidério"]
}

# 4. BARRA LATERAL (SIDEBAR)
st.sidebar.title("⚙️ Painel de Controle")
eng_selecionado = st.sidebar.selectbox("Engenheiro Responsável", list(mapa_prodin.keys()))
campus_selecionado = st.sidebar.selectbox("Campus", mapa_prodin[eng_selecionado])

st.sidebar.markdown("---")
choice = st.sidebar.radio("Navegação", ["Nova Inspeção", "Histórico de Registros"])

# Créditos dos Desenvolvedores na Barra Lateral
st.sidebar.markdown("---")
st.sidebar.info(f"""
**Desenvolvido por:**
* Thiago Messias Carvalho Soares
* Roger Ramos Santana

*PRODIN - IFBA 2026*
""")

if st.sidebar.button("Sair do Sistema"):
    st.session_state['autenticado'] = False
    st.rerun()

# 5. CONEXÃO E INTERFACE
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("📋 Inspeção Predial - IFBA")
st.subheader(f"📍 {campus_selecionado}")

if choice == "Nova Inspeção":
    with st.form("form_inspecao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            edificacao = st.text_input("Edificação / Bloco")
            disciplina = st.text_input("Disciplina (Ex: Civil, Elétrica)")
        with col2:
            data_ins = st.date_input("Data da Inspeção", datetime.now())
            ambiente = st.text_input("Ambiente / Sala")

        descricao = st.text_area("Descrição da Não Conformidade")
        solucoes = st.text_area("Sugestão de Solução / Encaminhamento")
        
        # Lógica de Captura: No celular permite tirar foto na hora ou escolher da galeria
        foto = st.file_uploader("📸 Tirar Foto ou Escolher da Galeria", type=['jpg', 'jpeg', 'png'])

        if st.form_submit_button("✅ Salvar Registro"):
            foto_base64 = ""
            
            if foto:
                with st.spinner("Processando imagem..."):
                    # Redimensiona a foto para não estourar o limite do Google Sheets
                    img = Image.open(foto)
                    img.thumbnail((800, 800)) 
                    buffered = io.BytesIO()
                    # Salva em JPEG com qualidade otimizada para ser leve
                    img.save(buffered, format="JPEG", quality=70)
                    foto_base64 = base64.b64encode(buffered.getvalue()).decode()

            # Preparação dos dados
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
            
            # Converte o Base64 de volta para imagem na tela
            if "Foto_Dados" in reg and reg["Foto_Dados"]:
                img_bytes = base64.b64decode(reg["Foto_Dados"])
                st.image(img_bytes, caption=f"Evidência - {reg['Ambiente']}", use_container_width=True)
            else:
                st.info("Este registro não possui foto anexa.")
    except Exception as e:
        st.error(f"Erro ao carregar o histórico: {e}")
