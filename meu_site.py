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

# 2. SISTEMA DE LOGIN (Senha: IFBA2026)
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
            st.error("Senha incorreta!")

if not st.session_state['autenticado']:
    login()
    st.stop()

# 3. FUNÇÃO DE UPLOAD PARA O DRIVE (COM CORREÇÃO DE COTA)
def upload_to_drive(file_path, file_name):
    try:
        info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=credentials)
        
        # ID da sua pasta compartilhada onde o robô é Editor
        folder_id = '1gh5qlrzuAqGoyG8X5MP813MAzD9DsDo-' 

        file_metadata = {
            'name': file_name, 
            'parents': [folder_id]
        }
        
        # 'resumable=True' resolve o erro de cota em contas de serviço
        media = MediaFileUpload(file_path, mimetype='image/jpeg', resumable=True)
        
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, webViewLink'
        ).execute()
        
        # Dá permissão de visualização para o link funcionar no histórico
        service.permissions().create(
            fileId=file.get('id'), 
            body={'type': 'anyone', 'role': 'viewer'}
        ).execute()
        
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Erro no Drive: {e}")
        return None

# 4. MAPEAMENTO COMPLETO (CONFORME BANNER PRODIN)
mapa_prodin = {
    "Eng. Thiago": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"],
    "Eng. Roger": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"],
    "Eng. Laís": ["Barreiras", "Jaguaquara", "Jequié"],
    "Eng. Larissa": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacã"],
    "Eng. Marcelo": ["Brumado", "Vitória da Conquista"],
    "Eng. Fenelon": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"],
    "Eng. do Local": ["Salvador", "Reitoria", "Polo de Inovação", "Salinas da Margarida", "São Desidério"]
}

# 5. BARRA LATERAL (SIDEBAR)
st.sidebar.title("⚙️ Painel de Controle")

# Seleção do Engenheiro
eng_selecionado = st.sidebar.selectbox("Engenheiro Responsável", list(mapa_prodin.keys()))

# Seleção do Campus (Filtrado pelo Engenheiro)
campus_selecionado = st.sidebar.selectbox("Campus", mapa_prodin[eng_selecionado])

st.sidebar.markdown("---")
choice = st.sidebar.radio("Navegação", ["Nova Inspeção", "Histórico de Registros"])

if st.sidebar.button("Sair"):
    st.session_state['autenticado'] = False
    st.rerun()

# 6. CONEXÃO E INTERFACE PRINCIPAL
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("📋 Inspeção Predial - IFBA")
st.info(f"📍 {campus_selecionado} | 👷 {eng_selecionado}")

if choice == "Nova Inspeção":
    with st.form("form_inspecao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            edificacao = st.text_input("Edificação / Bloco")
            disciplina = st.text_input("Disciplina (Ex: Civil)")
        with col2:
            data_ins = st.date_input("Data", datetime.now())
            ambiente = st.text_input("Ambiente / Sala")

        descricao = st.text_area("Descrição do Problema")
        solucoes = st.text_area("Sugestão de Solução")
        
        foto_arquivo = st.camera_input("📸 Foto da Evidência")

        if st.form_submit_button("✅ Salvar Registro"):
            link_foto = "Sem foto"
            if foto_arquivo:
                with st.spinner("Enviando foto ao Drive..."):
                    # Arquivo temporário
                    temp = f"temp_{datetime.now().timestamp()}.jpg"
                    with open(temp, "wb") as f: f.write(foto_arquivo.getbuffer())
                    
                    nome_f = f"Inspecao_{campus_selecionado}_{datetime.now().strftime('%d-%m-%y_%H-%M')}.jpg"
                    link_foto = upload_to_drive(temp, nome_f)
                    
                    if os.path.exists(temp): os.remove(temp)

            # Montagem do DataFrame para o Sheets (Colunas A a L)
            novo_dado = pd.DataFrame([{
                "Data": data_ins.strftime("%d/%m/%Y"),
                "Campus": campus_selecionado,
                "Edificacao": edificacao,
                "Disciplina": disciplina,
                "Ambiente": ambiente,
                "Descricao": descricao,
                "Solucoes": solucoes,
                "Foto": "Anexada" if foto_arquivo else "Nenhuma",
                "Engenheiro": eng_selecionado,
                "Link_Foto": link_foto
            }])

            # Atualiza a Planilha
            df_antigo = conn.read(ttl=0)
            df_final = pd.concat([df_antigo, novo_dado], ignore_index=True)
            conn.update(data=df_final)
            st.success("✅ Registro e Foto salvos com sucesso!")

elif choice == "Histórico de Registros":
    df = conn.read(ttl=0)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.divider()
        st.markdown("### Detalhes do Registro Selecionado")
        id_linha = st.selectbox("Selecione o ID para ver a foto:", df.index)
        reg = df.iloc[id_linha]
        
        # Exibe a foto se houver link válido
        if str(reg.get('Link_Foto', "")).startswith("http"):
            st.image(reg['Link_Foto'], caption=f"Evidência - {reg['Ambiente']}", use_container_width=True)
        else:
            st.warning("Este registro não possui foto.")
    else:
        st.warning("Nenhum dado encontrado na planilha.")

# RODAPÉ DE CRÉDITOS
st.sidebar.markdown("---")
st.sidebar.info(f"""
**Desenvolvido por:**
* Thiago Messias Carvalho Soares
* Roger Ramos Santana

*PRODIN - IFBA 2026*
""")
