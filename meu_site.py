import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import io

# 1. CONFIGURAÇÕES INICIAIS
st.set_page_config(page_title="Sistema de Inspeção IFBA", layout="centered")

# 2. CONEXÃO COM GOOGLE DRIVE (Para as Fotos)
def upload_to_drive(file_bytes, file_name):
    try:
        # Puxa as credenciais das Secrets do Streamlit
        info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=credentials)

        # ID da pasta "FOTOS DO PRODIN EM CAMPUS" que você criou
        folder_id = '1gh5qlrzuAqGoyG8X5MP813MAzD9DsDo-' 

        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(file_bytes, mimetype='image/jpeg')
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Erro no Drive: {e}")
        return None

# 3. CONEXÃO COM GOOGLE SHEETS (Para os Dados)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # ttl=0 garante que ele sempre leia a versão mais nova da planilha
    return conn.read(ttl=0)

# 4. INTERFACE DO USUÁRIO
st.title("📋 Inspeção Predial - IFBA")
st.subheader("Eng. Thiago Messias Carvalho Soares")

menu = ["Nova Inspeção", "Histórico"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Nova Inspeção":
    with st.form("form_inspecao"):
        col1, col2 = st.columns(2)
        with col1:
            engenheiro = st.selectbox("Engenheiro", ["Eng. Thiago", "Eng. Roger Ramos"])
            campus = st.selectbox("Campus", ["Euclides da Cunha", "Poções", "Feira de Santana"])
        with col2:
            data = st.date_input("Data da Inspeção", datetime.now())
            local = st.text_input("Local Exato (Ex: Sala 04)")

    problema = st.text_area("Descrição do Problema")
    gravidade = st.select_slider("Gravidade", options=["Leve", "Média", "Urgente"])
    
    # CAMPO DE FOTO
    foto_arquivo = st.camera_input("📸 Capturar Evidência Fotográfica")

    if st.form_submit_button("Salvar Inspeção"):
        link_foto = "Sem foto"
        if foto_arquivo:
            st.info("Enviando foto para o Google Drive...")
            # Converte a foto para bytes
            img_bytes = io.BytesIO(foto_arquivo.getvalue())
            nome_foto = f"Inspecao_{campus}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            
            # Salva no Drive e pega o link
            temp_path = f"temp_{nome_foto}"
            with open(temp_path, "wb") as f:
                f.write(foto_arquivo.getbuffer())
            
            link_foto = upload_to_drive(temp_path, nome_foto)
        
        # Salva na Planilha
        novo_dado = pd.DataFrame([{
            "Data": data.strftime("%d/%m/%Y"),
            "Engenheiro": engenheiro,
            "Campus": campus,
            "Local": local,
            "Problema": problema,
            "Gravidade": gravidade,
            "Foto": link_foto
        }])
        
        df_atual = load_data()
        df_final = pd.concat([df_atual, novo_dado], ignore_index=True)
        conn.update(data=df_final)
        st.success("✅ Inspeção salva com sucesso!")

elif choice == "Histórico":
    st.subheader("Registros Realizados")
    df = load_data()
    
    if not df.empty:
        # Seleção de Registro
        id_sel = st.selectbox("Selecione o ID para detalhes", df.index)
        reg_sel = df.iloc[id_sel]
        
        st.write(f"**Engenheiro:** {reg_sel['Engenheiro']}")
        st.write(f"**Problema:** {reg_sel['Problema']}")
        
        # --- TRAVA DE SEGURANÇA PARA A FOTO (Evita o erro vermelho) ---
        if 'Foto' in reg_sel and str(reg_sel['Foto']).startswith('http'):
            try:
                st.image(reg_sel['Foto'], caption=f"Evidência da Inspeção", width=500)
            except:
                st.warning("Link de imagem encontrado, mas não pôde ser exibido.")
        else:
            st.info("Nenhuma foto disponível para este registro.")
        # -------------------------------------------------------------
        
        st.dataframe(df)
    else:
        st.info("Nenhum dado encontrado.")

st.sidebar.markdown("---")
st.sidebar.write("Desenvolvido por: **Thiago Carvalho** & **Roger Ramos**")
