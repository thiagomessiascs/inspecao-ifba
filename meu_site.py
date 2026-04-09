import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image

# 1. Sistema de Autenticação
def verificar_senha():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if not st.session_state["autenticado"]:
        st.set_page_config(page_title="Login - Inspeção IFBA", page_icon="🔐")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔐 Acesso Restrito")
            st.subheader("Inspeção Predial IFBA")
            senha = st.text_input("Digite a senha de acesso:", type="password")
            if st.button("Entrar"):
                if senha == "IFBA2026":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
        return False
    return True

if verificar_senha():
    st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide", page_icon="🏗️")

    # --- CABEÇALHO ---
    url_logo_oficial = "https://portal.ifba.edu.br/proen/imagens/marcas-if/marcas-ifba-v/ifba-vertical.png"
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; background-color: #fcfcfc; padding: 25px; border-radius: 20px; border-left: 12px solid #2e7d32; border-bottom: 2px solid #e0e0e0; margin-bottom: 30px;">
            <img src="{url_logo_oficial}" style="width: 75px; height: 75px; border-radius: 50%; object-fit: contain; background: white; padding: 5px; border: 3px solid #2e7d32;">
            <div style="margin-left: 25px;">
                <h1 style="margin: 0; color: #1e4620; font-family: sans-serif; font-size: 36px;">Inspeção Predial IFBA</h1>
                <p style="margin: 0; color: #555; font-size: 16px;">Engenheiro Thiago Messias Carvalho Soares</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df_base = conn.read(ttl="0")
        # Garante que temos um índice limpo para a edição
        df_base = df_base.reset_index(drop=True)
    except:
        df_base = pd.DataFrame()

    with st.sidebar:
        st.header("🏢 Unidades IFBA")
        campi_ifba = sorted(["Salvador", "Feira de Santana", "Simões Filho", "Santo Amaro", "Barreiras", "Juazeiro", "Jequié", "Ilhéus"])
        campus_sel = st.selectbox("Selecione o Campus:", campi_ifba)
        
        # --- LÓGICA DE SELEÇÃO PARA EDIÇÃO ---
        st.markdown("---")
        st.subheader("🛠️ Modo de Edição")
        df_campus = df_base[df_base['Campus'] == campus_sel]
        
        edit_mode = False
        index_to_edit = None
        
        if not df_campus.empty:
            opcoes_edit = ["Nova Inspeção"] + [f"ID {i} - {row['Edificacao']}" for i, row in df_campus.iterrows()]
            selecao = st.selectbox("Selecione para editar:", opcoes_edit)
            
            if selecao != "Nova Inspeção":
                edit_mode = True
                index_to_edit = int(selecao.split(" ")[1])
                dados_edit = df_base.iloc[index_to_edit]

        if st.button("🚪 Sair"):
            st.session_state["autenticado"] = False
            st.rerun()

    # 4. Formulário (Adapta se for Novo ou Edição)
    with st.form("form_vistoria", clear_on_submit=not edit_mode):
        titulo_form = f"✏️ Editando: {dados_edit['Edificacao']}" if edit_mode else f"📝 Nova Vistoria: {campus_sel}"
        st.subheader(titulo_form)
        
        c1, c2 = st.columns(2)
        with c1:
            # Se estiver editando, os campos iniciam com o valor atual (value)
            edificacao = st.text_input("Edificação/Bloco:", value=dados_edit['Edificacao'] if edit_mode else "", key="edif")
            disciplina_lista = ["Alvenaria", "Estrutura", "Elétrica", "Hidráulica", "Pintura", "Cobertura"]
            idx_disc = disciplina_lista.index(dados_edit['Disciplina']) if edit_mode and dados_edit['Disciplina'] in disciplina_lista else 0
            disciplina = st.selectbox("Disciplina:", disciplina_lista, index=idx_disc)
            
            ambiente = st.text_input("Ambiente/Local:", value=dados_edit['Ambiente'] if edit_mode else "")
            descricao = st.text_area("Descrição da Patologia:", value=dados_edit['Descricao'] if edit_mode else "")
            solucoes = st.text_area("Soluções Sugeridas:", value=dados_edit['Solucoes'] if edit_mode else "")
            
        with c2:
            st.write("**📸 Evidência Fotográfica**")
            foto_upload = st.file_uploader("Arraste a nova foto (opcional)", type=["jpg", "png", "jpeg"])
            if edit_mode and not foto_upload:
                st.warning(f"Status atual da foto: {dados_edit['Foto']}")
            
            st.write("**Avaliação GUT**")
            g = st.slider("Gravidade", 1, 5, int(dados_edit['Score_GUT']**(1/3)) if edit_mode else 3, key="g")
            u = st.slider("Urgência", 1, 5, 3, key="u")
            t = st.slider("Tendência", 1, 5, 3, key="t")
            score = g * u * t
            status = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
            st.metric("Prioridade", status, f"Score: {score}")

        btn_label = "💾 Atualizar Registro" if edit_mode else "💾 Salvar Nova Inspeção"
        if st.form_submit_button(btn_label):
            nova_linha = {
                "Data": dados_edit['Data'] if edit_mode else datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Campus": campus_sel,
                "Edificacao": edificacao,
                "Disciplina": disciplina,
                "Ambiente": ambiente,
                "Descricao": descricao,
                "Solucoes": solucoes,
                "Foto": "Anexada" if foto_upload else (dados_edit['Foto'] if edit_mode else "Sem foto"),
                "Score_GUT": score,
                "Status": status
            }
            
            if edit_mode:
                df_base.iloc[index_to_edit] = nova_linha
            else:
                df_base = pd.concat([df_base, pd.DataFrame([nova_linha])], ignore_index=True)
            
            conn.update(data=df_base)
            st.success("✅ Histórico atualizado com sucesso!")
            st.rerun()

    # 5. Tabela de Histórico
    if not df_base.empty:
        df_filtrado = df_base[df_base['Campus'] == campus_sel]
        if not df_filtrado.empty:
            st.markdown("---")
            st.subheader(f"📋 Histórico de Inspeções - {campus_sel}")
            # Mostra o ID para facilitar a edição
            st.dataframe(df_filtrado, use_container_width=True)

    st.markdown("---")
    st.markdown(f"<p style='text-align: center; color: gray;'>Engenheiro <b>Thiago Messias Carvalho Soares</b> - IFBA 2026</p>", unsafe_allow_html=True)
     
