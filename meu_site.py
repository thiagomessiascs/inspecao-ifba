import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# --- 1. CONFIGURAÇÕES DA EQUIPE E DRIVE ---
EQUIPE = {
    "Eng. Thiago": {"campi": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"], "foto": "https://github.com/thiagomessiascs/inspecao-ifba/blob/main/Thiago.jpg?raw=true"},
    "Eng. Roger": {"campi": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"], "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"},
    "Eng. Laís": {"campi": ["Barreiras", "Jaguaquara", "Jequié"], "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135768.png"},
    "Eng. Larissa": {"campi": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacã"], "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135768.png"},
    "Eng. Marcelo": {"campi": ["Brumado", "Vitória da Conquista"], "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"},
    "Eng. Fenelon": {"campi": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"], "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"}
}

DADOS_TECNICOS = {
    "Alvenaria": {"patologias": ["Fissura/Trinca", "Umidade", "Desplacamento"], "solucoes": ["Tratamento tela", "Impermeabilização", "Reboco"]},
    "Estrutura": {"patologias": ["Corrosão armadura", "Segregação concreto"], "solucoes": ["Escarificação", "Reforço"]},
    "Elétrica": {"patologias": ["Fiação exposta", "Disjuntor"], "solucoes": ["Revisão", "Troca"]},
    "Hidrossanitária": {"patologias": ["Vazamento", "Entupimento"], "solucoes": ["Troca reparo", "Desobstrução"]},
    "Outros": {"patologias": ["Outros"], "solucoes": ["Outros"]}
}

# CONFIGURAÇÕES DO DRIVE (Substitua pelo seu ID real do print)
FOLDER_ID = "1gh5qlrzuAqGoyG8X5MP813MAzD9DsDo-"

# Função para autenticar e fazer upload
def upload_foto(file):
    if file is not None:
        try:
            # Puxando a chave JSON das Secrets do Streamlit (Segurança)
            info = st.secrets["gcp_service_account"]
            creds = service_account.Credentials.from_service_account_info(info)
            service = build('drive', 'v3', credentials=creds)
            
            file_metadata = {'name': file.name, 'parents': [FOLDER_ID]}
            media = MediaIoBaseUpload(io.BytesIO(file.getvalue()), mimetype=file.type)
            
            uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return f"https://drive.google.com/uc?export=view&id={uploaded_file.get('id')}"
        except Exception as e:
            st.error(f"Erro no upload: {e}")
    return "Sem foto"

st.set_page_config(page_title="PRODIN - Inspeção Predial", layout="wide")

# --- 2. DIALOG DE EDIÇÃO ---
@st.dialog("✏️ Editar Registro")
def editar_registro(index, row_data, conn, df_full):
    st.write(f"Editando item ID: **{index}**")
    
    # Mostrar foto atual se existir
    if row_data['Foto'] != "Sem foto":
        st.image(row_data['Foto'], caption="Evidência Atual", width=300)
    
    new_edif = st.selectbox("Edificação:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca", "Muro"], 
                            index=["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca", "Muro"].index(row_data['Edificacao']))
    new_desc = st.text_area("Descrição:", value=row_data['Descricao'])
    new_sol = st.text_area("Solução:", value=row_data['Solucoes'])
    new_foto = st.file_uploader("Substituir Foto?", type=['jpg', 'png', 'jpeg'])

    if st.button("Salvar Alterações"):
        df_full.loc[index, "Edificacao"] = new_edif
        df_full.loc[index, "Descricao"] = new_desc
        df_full.loc[index, "Solucoes"] = new_sol
        if new_foto:
            df_full.loc[index, "Foto"] = upload_foto(new_foto)
        
        conn.update(data=df_full)
        st.success("Atualizado!")
        st.rerun()

# --- 3. LOGIN ---
if "login" not in st.session_state: st.session_state.login = False
if not st.session_state.login:
    st.title("🔐 Login PRODIN")
    if st.text_input("Senha:", type="password") == "IFBA2026":
        if st.button("Acessar"): st.session_state.login = True; st.rerun()
else:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(ttl="0")

    with st.sidebar:
        eng_sel = st.selectbox("Engenheiro:", list(EQUIPE.keys()))
        col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
        with col_img2: st.image(EQUIPE[eng_sel]["foto"], width=100)
        campus_sel = st.selectbox("Campus:", sorted(EQUIPE[eng_sel]["campi"]))
        if st.button("Sair"): st.session_state.login = False; st.rerun()

    # --- 4. FORMULÁRIO ---
    st.markdown(f'# 🏢 Inspeção {campus_sel}')
    
    with st.expander("📝 Novo Registro", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            edif = st.selectbox("Edificação:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca", "Muro"])
            disc = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()))
            pat_sug = st.selectbox("Sugestão de Patologia:", DADOS_TECNICOS[disc]["patologias"])
            desc = st.text_area("Descrição:", value=pat_sug if pat_sug != "Outros" else "")
        with c2:
            sol_sug = st.selectbox("Sugestão de Solução:", DADOS_TECNICOS[disc]["solucoes"])
            sol = st.text_area("Solução:", value=sol_sug if sol_sug != "Outros" else "")
            arq_foto = st.file_uploader("📸 Capturar Evidência Fotográfica", type=['png', 'jpg', 'jpeg'])
        
        if st.button("💾 Salvar Inspeção"):
            link_foto = upload_foto(arq_foto)
            novo_item = {
                "Data": datetime.now().strftime("%d/%m/%Y"), "Engenheiro": eng_sel, "Campus": campus_sel,
                "Edificacao": edif, "Disciplina": disc, "Descricao": desc, "Solucoes": sol, "Foto": link_foto
            }
            df_final = pd.concat([df_base, pd.DataFrame([novo_item])], ignore_index=True)
            conn.update(data=df_final)
            st.success("Salvo com sucesso!")
            st.rerun()

    # --- 5. HISTÓRICO ---
    st.markdown("---")
    df_campus = df_base[df_base['Campus'] == campus_sel].copy()
    
    if not df_campus.empty:
        st.dataframe(df_campus[["Edificacao", "Disciplina", "Descricao"]].tail(5), use_container_width=True)
        id_sel = st.selectbox("Visualizar/Gerenciar ID:", df_campus.index)
        
        # MOSTRAR FOTO NA INTERFACE
        reg_sel = df_base.loc[id_sel]
        if reg_sel['Foto'] != "Sem foto":
            st.image(reg_sel['Foto'], caption=f"Evidência do ID {id_sel}", width=400)
        
        b1, b2, _ = st.columns([1, 1, 3])
        with b1:
            if st.button("✏️ Editar"): editar_registro(id_sel, reg_sel, conn, df_base)
        with b2:
            if st.button("🗑️ Excluir"):
                conn.update(data=df_base.drop(id_sel))
                st.rerun()

    # --- RODAPÉ ---
    st.markdown("---")
    st.markdown('<div style="text-align:center; color:#888; font-size:12px;"><b>Desenvolvedores:</b> Thiago M. C. Soares & Roger R. Santana <br> PRODIN - IFBA 2026</div>', unsafe_allow_html=True)
