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

# 2. FUNÇÃO PARA UPLOAD NO GOOGLE DRIVE
def upload_to_drive(file_path, file_name):
    try:
        # Puxa credenciais das Secrets
        info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=credentials)

        # ID da pasta "FOTOS DO PRODIN EM CAMPUS"
        folder_id = '1gh5qlrzuAqGoyG8X5MP813MAzD9DsDo-' 

        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(file_path, mimetype='image/jpeg')
        
        # Cria o arquivo no Drive
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        # Torna a foto pública para que apareça no App (Visualizador)
        service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'viewer'}).execute()
        
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Erro ao enviar para o Drive: {e}")
        return None

# 3. CONEXÃO COM GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # ttl=0 força o Streamlit a ler a planilha em tempo real
    return conn.read(ttl=0)

# 4. INTERFACE E MENU
st.title("📋 Sistema de Inspeção Predial")
st.markdown("### IFBA - Engenharia de Manutenção")

menu = ["Nova Inspeção", "Histórico de Registros"]
choice = st.sidebar.selectbox("Navegação", menu)

if choice == "Nova Inspeção":
    st.info("Preencha os dados abaixo para gerar um novo registro.")
    
    with st.form("form_inspecao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            engenheiro = st.selectbox("Engenheiro Responsável", ["Eng. Thiago Messias Carvalho Soares", "Eng. Roger Ramos Santana"])
            campus = st.selectbox("Campus", ["Euclides da Cunha", "Poções", "Feira de Santana", "Barreiras", "Brumado"])
            edificacao = st.text_input("Edificação / Bloco")
        with col2:
            data_inspecao = st.date_input("Data da Inspeção", datetime.now())
            disciplina = st.text_input("Disciplina (Ex: Hidráulica, Civil)")
            ambiente = st.text_input("Ambiente / Sala")

        descricao = st.text_area("Descrição do Problema Detectado")
        solucoes = st.text_area("Sugestão de Solução / Encaminhamento")
        
        # Captura de Foto
        foto_arquivo = st.camera_input("📸 Registrar Evidência (Foto)")

        if st.form_submit_button("✅ Finalizar e Salvar Registro"):
            link_drive = "Sem foto"
            
            if foto_arquivo:
                with st.spinner("Enviando imagem para o servidor..."):
                    # Salva arquivo temporário para o upload
                    temp_name = f"temp_{datetime.now().timestamp()}.jpg"
                    with open(temp_name, "wb") as f:
                        f.write(foto_arquivo.getbuffer())
                    
                    nome_final_foto = f"Inspecao_{campus}_{datetime.now().strftime('%d-%m-%Y_%H-%M')}.jpg"
                    link_drive = upload_to_drive(temp_name, nome_final_foto)
                    
                    if os.path.exists(temp_name):
                        os.remove(temp_name)

            # Prepara os dados conforme as colunas da sua planilha (H e L inclusas)
            novo_dado = pd.DataFrame([{
                "Data": data_inspecao.strftime("%d/%m/%Y"),
                "Campus": campus,
                "Edificacao": edificacao,
                "Disciplina": disciplina,
                "Ambiente": ambiente,
                "Descricao": descricao,
                "Solucoes": solucoes,
                "Foto": "Anexada" if foto_arquivo else "Nenhuma",
                "Engenheiro": engenheiro,
                "Link_Foto": link_drive
            }])

            # Atualiza a planilha
            df_existente = load_data()
            df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
            conn.update(data=df_final)
            
            st.success("Dados salvos com sucesso na planilha e foto armazenada no Drive!")

elif choice == "Histórico de Registros":
    st.subheader("Consultar Inspeções Realizadas")
    df = load_data()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.markdown("#### Detalhes do Registro Selecionado")
        id_linha = st.selectbox("Escolha o índice (ID) para ver a foto:", df.index)
        
        registro = df.iloc[id_linha]
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.write(f"**Local:** {registro['Edificacao']} - {registro['Ambiente']}")
            st.write(f"**Descrição:** {registro['Descricao']}")
            st.write(f"**Engenheiro:** {registro['Engenheiro']}")
        
        with c2:
            # Lógica de segurança para exibir a foto
            link_foto = registro.get('Link_Foto', "Sem link")
            if str(link_foto).startswith("http"):
                st.image(link_foto, caption="Foto da Evidência", use_container_width=True)
            else:
                st.warning("Não há foto disponível para este registro.")
    else:
        st.warning("Nenhum registro encontrado na base de dados.")

# 5. RODAPÉ DE CRÉDITOS
st.sidebar.markdown("---")
st.sidebar.info(f"""
**Desenvolvido por:**
* Thiago Messias Carvalho Soares
* Roger Ramos Santana

*IFBA - 2026*
""")
