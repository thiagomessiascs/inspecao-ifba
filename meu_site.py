import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import io
import os

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Sistema de Inspeção IFBA", layout="centered", page_icon="📋")

# 2. SISTEMA DE LOGIN
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

def login():
    st.title("🔐 Acesso Restrito - IFBA")
    senha = st.text_input("Digite a senha de acesso:", type="password")
    if st.button("Entrar"):
        if senha == "IFBA2026":
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("Senha incorreta! Tente novamente.")

if not st.session_state['autenticado']:
    login()
    st.stop()

# --- ÁREA RESTRITA ---

# 3. FUNÇÃO PARA UPLOAD NO GOOGLE DRIVE
def upload_to_drive(file_path, file_name):
    try:
        info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=credentials)
        folder_id = '1gh5qlrzuAqGoyG8X5MP813MAzD9DsDo-' 

        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(file_path, mimetype='image/jpeg')
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'viewer'}).execute()
        
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Erro ao enviar para o Drive: {e}")
        return None

# 4. CONEXÃO COM GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(ttl=0)

# 5. CONFIGURAÇÃO DOS ENGENHEIROS E CAMPI NA BARRA LATERAL
st.sidebar.title("⚙️ Configurações")

# Dicionário relacionando Campus -> Engenheiro
mapa_campus_eng = {
    "Poções": "Eng. Thiago Messias Carvalho Soares",
    "Feira de Santana": "Eng. Thiago Messias Carvalho Soares",
    "Euclides da Cunha": "Eng. Thiago Messias Carvalho Soares",
    "Barreiras": "Eng. Roger Ramos Santana",
    "Brumado": "Eng. Roger Ramos Santana",
    "Jacobina": "Eng. Roger Ramos Santana"
}

# Seleção do Campus na Lateral
campus_selecionado = st.sidebar.selectbox("Selecione o Campus da Inspeção", list(mapa_campus_eng.keys()))

# Define o Engenheiro automaticamente baseado no Campus selecionado
engenheiro_responsavel = mapa_campus_eng[campus_selecionado]

st.sidebar.markdown(f"**Engenheiro Responsável:** \n\n {engenheiro_responsavel}")

# Navegação entre abas
st.sidebar.markdown("---")
choice = st.sidebar.radio("Navegação", ["Nova Inspeção", "Histórico de Registros"])

if st.sidebar.button("Sair/Logout"):
    st.session_state['autenticado'] = False
    st.rerun()

# 6. INTERFACE PRINCIPAL
st.title("📋 Sistema de Inspeção Predial")
st.markdown(f"**Campus:** {campus_selecionado} | **Responsável:** {engenheiro_responsavel}")

if choice == "Nova Inspeção":
    with st.form("form_inspecao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            edificacao = st.text_input("Edificação / Bloco")
            disciplina = st.text_input("Disciplina (Ex: Hidráulica)")
        with col2:
            data_inspecao = st.date_input("Data da Inspeção", datetime.now())
            ambiente = st.text_input("Ambiente / Sala")

        descricao = st.text_area("Descrição do Problema Detectado")
        solucoes = st.text_area("Sugestão de Solução")
        
        foto_arquivo = st.camera_input("📸 Registrar Foto da Evidência")

        if st.form_submit_button("✅ Salvar Registro"):
            link_drive = "Sem foto"
            if foto_arquivo:
                with st.spinner("Enviando foto ao Drive..."):
                    temp_name = f"temp_{datetime.now().timestamp()}.jpg"
                    with open(temp_name, "wb") as f:
                        f.write(foto_arquivo.getbuffer())
                    
                    nome_f = f"Inspecao_{campus_selecionado}_{datetime.now().strftime('%d-%m-%Y_%H-%M')}.jpg"
                    link_drive = upload_to_drive(temp_name, nome_f)
                    if os.path.exists(temp_name): os.remove(temp_name)

            # Salva na planilha respeitando a ordem das colunas (Data, Campus, Edificacao, Disciplina, Ambiente, Descricao, Solucoes, Foto, Engenheiro, Link_Foto)
            novo_dado = pd.DataFrame([{
                "Data": data_inspecao.strftime("%d/%m/%Y"),
                "Campus": campus_selecionado,
                "Edificacao": edificacao,
                "Disciplina": disciplina,
                "Ambiente": ambiente,
                "Descricao": descricao,
                "Solucoes": solucoes,
                "Foto": "Anexada" if foto_arquivo else "Nenhuma",
                "Engenheiro": engenheiro_responsavel,
                "Link_Foto": link_drive
            }])

            df_final = pd.concat([load_data(), novo_dado], ignore_index=True)
            conn.update(data=df_final)
            st.success("✅ Registro e Foto salvos com sucesso!")

elif choice == "Histórico de Registros":
    df = load_data()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.divider()
        st.markdown("### Detalhes do Registro")
        id_linha = st.selectbox("Selecione o ID para análise:", df.index)
        reg = df.iloc[id_linha]
        
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Campus:** {reg['Campus']}")
            st.write(f"**Engenheiro:** {reg['Engenheiro']}")
            st.write(f"**Problema:** {reg['Descricao']}")
        with c2:
            link = reg.get('Link_Foto', "")
            if str(link).startswith("http"):
                st.image(link, caption="Foto da Evidência", use_container_width=True)
            else:
                st.warning("Registro sem foto anexada.")

# RODAPÉ
st.sidebar.markdown("---")
st.sidebar.info(f"""
**Desenvolvido por:**
* Thiago Messias Carvalho Soares
* Roger Ramos Santana

*IFBA - 2026*
""")
