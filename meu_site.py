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
        info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=credentials)

        # ID da sua pasta FOTOS DO PRODIN EM CAMPUS
        folder_id = '1gh5qlrzuAqGoyG8X5MP813MAzD9DsDo-' 

        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(file_path, mimetype='image/jpeg')
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'viewer'}).execute()
        
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Erro ao enviar para o Drive: {e}")
        return None

# 3. CONEXÃO COM GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(ttl=0)

# 4. MAPEAMENTO DE ENGENHEIROS POR CAMPUS
# Adicione ou altere os nomes conforme a escala real
mapa_engenheiros = {
    "Poções": "Eng. Thiago Messias Carvalho Soares",
    "Feira de Santana": "Eng. Thiago Messias Carvalho Soares",
    "Barreiras": "Eng. Roger Ramos Santana",
    "Brumado": "Eng. Roger Ramos Santana",
    "Euclides da Cunha": "Eng. Thiago Messias Carvalho Soares",
    "Jacobina": "Eng. Roger Ramos Santana"
}

# 5. INTERFACE
st.title("📋 Sistema de Inspeção Predial")
st.markdown("### IFBA - Engenharia de Manutenção")

menu = ["Nova Inspeção", "Histórico de Registros"]
choice = st.sidebar.selectbox("Navegação", menu)

if choice == "Nova Inspeção":
    st.info("Preencha os dados abaixo para gerar um novo registro.")
    
    with st.form("form_inspecao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Seleção de Campus primeiro para sugerir o engenheiro
            campus_selecionado = st.selectbox("Campus", list(mapa_engenheiros.keys()))
            
            # Sugere o engenheiro com base no campus, mas permite trocar
            lista_engenheiros = ["Eng. Thiago Messias Carvalho Soares", "Eng. Roger Ramos Santana"]
            eng_sugerido = mapa_engenheiros.get(campus_selecionado)
            index_padrao = lista_engenheiros.index(eng_sugerido) if eng_sugerido in lista_engenheiros else 0
            
            engenheiro = st.selectbox("Engenheiro Responsável", lista_engenheiros, index=index_padrao)
            edificacao = st.text_input("Edificação / Bloco")
            
        with col2:
            data_inspecao = st.date_input("Data da Inspeção", datetime.now())
            disciplina = st.text_input("Disciplina (Ex: Hidráulica, Civil)")
            ambiente = st.text_input("Ambiente / Sala")

        descricao = st.text_area("Descrição do Problema Detectado")
        solucoes = st.text_area("Sugestão de Solução")
        
        foto_arquivo = st.camera_input("📸 Registrar Foto")

        if st.form_submit_button("✅ Finalizar e Salvar Registro"):
            link_drive = "Sem foto"
            
            if foto_arquivo:
                with st.spinner("Enviando imagem..."):
                    temp_name = f"temp_{datetime.now().timestamp()}.jpg"
                    with open(temp_name, "wb") as f:
                        f.write(foto_arquivo.getbuffer())
                    
                    nome_final_foto = f"Inspecao_{campus_selecionado}_{datetime.now().strftime('%d-%m-%Y_%H-%M')}.jpg"
                    link_drive = upload_to_drive(temp_name, nome_final_foto)
                    if os.path.exists(temp_name): os.remove(temp_name)

            # Salva exatamente nas colunas da sua planilha (A até L)
            novo_dado = pd.DataFrame([{
                "Data": data_inspecao.strftime("%d/%m/%Y"),
                "Campus": campus_selecionado,
                "Edificacao": edificacao,
                "Disciplina": disciplina,
                "Ambiente": ambiente,
                "Descricao": descricao,
                "Solucoes": solucoes,
                "Foto": "Anexada" if foto_arquivo else "Nenhuma",
                "Engenheiro": engenheiro,
                "Link_Foto": link_drive
            }])

            df_final = pd.concat([load_data(), novo_dado], ignore_index=True)
            conn.update(data=df_final)
            st.success("✅ Registro salvo com sucesso!")

elif choice == "Histórico de Registros":
    df = load_data()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.divider()
        id_linha = st.selectbox("Selecione o ID para ver detalhes e foto:", df.index)
        reg = df.iloc[id_linha]
        
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Campus:** {reg['Campus']}")
            st.write(f"**Engenheiro:** {reg['Engenheiro']}")
            st.write(f"**Local:** {reg['Edificacao']} - {reg['Ambiente']}")
            st.write(f"**Descrição:** {reg['Descricao']}")
        with c2:
            link = reg.get('Link_Foto', "")
            if str(link).startswith("http"):
                st.image(link, caption="Evidência Fotográfica", use_container_width=True)
            else:
                st.warning("Sem foto disponível.")
    else:
        st.warning("Nenhum registro encontrado.")

# 6. RODAPÉ DE CRÉDITOS
st.sidebar.markdown("---")
st.sidebar.info(f"""
**Desenvolvido por:**
* Thiago Messias Carvalho Soares
* Roger Ramos Santana

*IFBA - 2026*
""")
