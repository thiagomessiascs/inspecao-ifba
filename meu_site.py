import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import os

# 1. CONFIGURAÇÕES INICIAIS
st.set_page_config(page_title="Sistema de Inspeção IFBA", layout="centered", page_icon="📋")

# 🚨 IMPORTANTE: Verifique se o link da sua planilha termina com /edit#gid=0 ou algo parecido
# O link deve ser o que você copia da barra de endereços do navegador
URL_PLANILHA = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"

# 2. LOGIN
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acesso IFBA")
    senha = st.text_input("Senha:", type="password")
    if st.button("Entrar"):
        if senha == "IFBA2026":
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# 3. UPLOAD DRIVE (VERSÃO SEM ERRO DE COTA)
def upload_to_drive(file_path, file_name):
    try:
        info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=credentials)
        
        folder_id = '1gh5qlrzuAqGoyG8X5MP813MAzD9DsDo-' 

        file_metadata = {
            'name': file_name, 
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(file_path, mimetype='image/jpeg', resumable=True)
        
        # Criar o arquivo
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, webViewLink'
        ).execute()
        
        # Compartilhar para visualização
        service.permissions().create(
            fileId=file.get('id'), 
            body={'type': 'anyone', 'role': 'viewer'}
        ).execute()
        
        return file.get('webViewLink')
    except Exception as e:
        # Se der erro de cota, vamos tentar avisar de forma clara
        if "storageQuotaExceeded" in str(e):
            st.error("Erro de Espaço: O robô não conseguiu usar o seu armazenamento. Verifique se você deu permissão de EDITOR para o e-mail do robô na pasta do Drive.")
        else:
            st.error(f"Erro no Drive: {e}")
        return None

# 4. MAPEAMENTO PRODIN
mapa_prodin = {
    "Eng. Thiago": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"],
    "Eng. Roger": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"],
    "Eng. Laís": ["Barreiras", "Jaguaquara", "Jequié"],
    "Eng. Larissa": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacã"],
    "Eng. Marcelo": ["Brumado", "Vitória da Conquista"],
    "Eng. Fenelon": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"],
    "Eng. do Local": ["Salvador", "Reitoria", "Polo de Inovação", "Salinas da Margarida", "São Desidério"]
}

# 5. SIDEBAR
st.sidebar.title("⚙️ PRODIN")
eng_sel = st.sidebar.selectbox("Engenheiro", list(mapa_prodin.keys()))
campus_sel = st.sidebar.selectbox("Campus", mapa_prodin[eng_sel])
choice = st.sidebar.radio("Menu", ["Nova Inspeção", "Histórico"])

# 6. CONEXÃO SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

if choice == "Nova Inspeção":
    with st.form("form_inspecao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            edificacao = st.text_input("Edificação")
            disciplina = st.text_input("Disciplina")
        with col2:
            data_ins = st.date_input("Data", datetime.now())
            ambiente = st.text_input("Ambiente")
        
        desc = st.text_area("Descrição")
        sol = st.text_area("Solução")
        foto = st.camera_input("📸 Foto")

        if st.form_submit_button("Salvar Registro"):
            link_f = "Sem foto"
            if foto:
                tmp = f"temp_{datetime.now().timestamp()}.jpg"
                with open(tmp, "wb") as f: f.write(foto.getbuffer())
                link_f = upload_to_drive(tmp, f"Foto_{campus_sel}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.jpg")
                if os.path.exists(tmp): os.remove(tmp)

            if link_f or not foto: # Só salva se a foto deu certo ou se não tirou foto
                novo = pd.DataFrame([{
                    "Data": data_ins.strftime("%d/%m/%Y"), "Campus": campus_sel, "Edificacao": edificacao,
                    "Disciplina": disciplina, "Ambiente": ambiente, "Descricao": desc, "Solucoes": sol,
                    "Foto": "Sim" if foto else "Não", "Engenheiro": eng_sel, "Link_Foto": link_f
                }])

                try:
                    df_atual = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
                    df_final = pd.concat([df_atual, novo], ignore_index=True)
                    conn.update(spreadsheet=URL_PLANILHA, data=df_final)
                    st.success("✅ Registro salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar na planilha: {e}")

elif choice == "Histórico":
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        st.dataframe(df)
        if not df.empty:
            id_sel = st.selectbox("Ver foto do ID:", df.index)
            link = df.iloc[id_sel].get('Link_Foto', "")
            if str(link).startswith("http"):
                st.image(link)
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")

st.sidebar.info("Thiago & Roger - 2026")
