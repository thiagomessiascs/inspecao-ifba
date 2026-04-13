import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import os

# 1. CONFIGURAÇÕES BÁSICAS
st.set_page_config(page_title="Sistema de Inspeção IFBA", layout="centered", page_icon="📋")

# 🔗 COLOQUE O LINK DA SUA PLANILHA AQUI
URL_PLANILHA = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"

# 2. CONTROLE DE ACESSO
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acesso Restrito - PRODIN")
    senha = st.text_input("Digite a senha:", type="password")
    if st.button("Entrar"):
        if senha == "IFBA2026":
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# 3. FUNÇÃO DE UPLOAD (CONTORNO DE COTA)
def upload_to_drive(file_path, file_name):
    try:
        info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=credentials)
        
        # ID da sua pasta de fotos
        folder_id = '1gh5qlrzuAqGoyG8X5MP813MAzD9DsDo-' 

        file_metadata = {
            'name': file_name, 
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(file_path, mimetype='image/jpeg', resumable=True)
        
        # Criar o arquivo forçando o suporte a drives compartilhados
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, webViewLink',
            supportsAllDrives=True
        ).execute()
        
        # Permissão pública para o link da imagem funcionar no app
        service.permissions().create(
            fileId=file.get('id'), 
            body={'type': 'anyone', 'role': 'viewer'},
            supportsAllDrives=True
        ).execute()
        
        return file.get('webViewLink')
    except Exception as e:
        if "storageQuotaExceeded" in str(e):
            st.error("⚠️ Erro de Espaço (Cota): O Google bloqueou o robô. Tente usar uma pasta criada em um GMAIL PESSOAL.")
        else:
            st.error(f"❌ Erro no Drive: {e}")
        return None

# 4. MAPEAMENTO DE ENGENHEIROS E CAMPI
mapa_prodin = {
    "Eng. Thiago": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"],
    "Eng. Roger": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"],
    "Eng. Laís": ["Barreiras", "Jaguaquara", "Jequié"],
    "Eng. Larissa": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacã"],
    "Eng. Marcelo": ["Brumado", "Vitória da Conquista"],
    "Eng. Fenelon": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"],
    "Eng. do Local": ["Salvador", "Reitoria", "Polo de Inovação", "Salinas da Margarida", "São Desidério"]
}

# 5. MENU LATERAL
st.sidebar.title("⚙️ Painel PRODIN")
eng_selecionado = st.sidebar.selectbox("Engenheiro Responsável", list(mapa_prodin.keys()))
campus_selecionado = st.sidebar.selectbox("Campus", mapa_prodin[eng_selecionado])
choice = st.sidebar.radio("Navegação", ["Nova Inspeção", "Histórico de Registros"])

if st.sidebar.button("Sair"):
    st.session_state['autenticado'] = False
    st.rerun()

# 6. CONEXÃO COM GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("📋 Sistema de Inspeção Predial")
st.info(f"📍 **Campus:** {campus_selecionado} | 👷 **Responsável:** {eng_selecionado}")

if choice == "Nova Inspeção":
    with st.form("form_inspecao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            edificacao = st.text_input("Edificação / Bloco")
            disciplina = st.text_input("Disciplina (Ex: Hidráulica)")
        with col2:
            data_ins = st.date_input("Data da Inspeção", datetime.now())
            ambiente = st.text_input("Ambiente / Sala")

        descricao = st.text_area("Descrição do Problema")
        solucoes = st.text_area("Sugestão de Solução")
        
        foto_arquivo = st.camera_input("📸 Registrar Foto da Evidência")

        if st.form_submit_button("✅ Salvar Registro"):
            link_drive = "Sem foto"
            sucesso_upload = True
            
            if foto_arquivo:
                with st.spinner("Enviando foto ao Drive..."):
                    temp_path = f"temp_{datetime.now().timestamp()}.jpg"
                    with open(temp_path, "wb") as f:
                        f.write(foto_arquivo.getbuffer())
                    
                    nome_f = f"Inspecao_{campus_selecionado}_{datetime.now().strftime('%d-%m-%Y_%H-%M')}.jpg"
                    link_drive = upload_to_drive(temp_path, nome_f)
                    
                    if os.path.exists(temp_path): os.remove(temp_path)
                    if link_drive is None: sucesso_upload = False

            if sucesso_upload:
                # Criar nova linha (Colunas A até L)
                novo_registro = pd.DataFrame([{
                    "Data": data_ins.strftime("%d/%m/%Y"),
                    "Campus": campus_selecionado,
                    "Edificacao": edificacao,
                    "Disciplina": disciplina,
                    "Ambiente": ambiente,
                    "Descricao": descricao,
                    "Solucoes": solucoes,
                    "Foto": "Anexada" if foto_arquivo else "Nenhuma",
                    "Engenheiro": eng_selecionado,
                    "Link_Foto": link_drive
                }])

                try:
                    df_atual = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
                    df_final = pd.concat([df_atual, novo_registro], ignore_index=True)
                    conn.update(spreadsheet=URL_PLANILHA, data=df_final)
                    st.success("✅ Tudo salvo com sucesso na planilha e no Drive!")
                except Exception as e:
                    st.error(f"Erro ao salvar na planilha: {e}")

elif choice == "Histórico de Registros":
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.divider()
            id_linha = st.selectbox("Selecione o ID para ver detalhes e foto:", df.index)
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
                    st.warning("Sem foto para este registro.")
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")

# RODAPÉ
st.sidebar.markdown("---")
st.sidebar.info("Thiago Carvalho & Roger Ramos\n\nPRODIN - IFBA 2026")
