import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import base64
from io import BytesIO
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
                if senha == "IFBA2026": # Senha padrão
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
        <div style="display: flex; align-items: center; background-color: #fcfcfc; padding: 25px; border-radius: 20px; border-left: 12px solid #2e7d32; border-bottom: 2px solid #e0e0e0; margin-bottom: 30px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
            <img src="{url_logo_oficial}" style="width: 75px; height: 75px; border-radius: 50%; object-fit: contain; background: white; padding: 5px; border: 3px solid #2e7d32;">
            <div style="margin-left: 25px;">
                <h1 style="margin: 0; color: #1e4620; font-family: sans-serif; font-size: 36px;">Inspeção Predial IFBA</h1>
                <p style="margin: 0; color: #555; font-size: 16px;">Engenharia, Manutenção e Vistorias Técnicas</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df_base = conn.read(ttl="0")
    except:
        df_base = pd.DataFrame()

    with st.sidebar:
        st.header("🏢 Unidades IFBA")
        campi_ifba = sorted(["Salvador", "Feira de Santana", "Simões Filho", "Santo Amaro", "Barreiras", "Juazeiro"]) # Lista resumida para exemplo
        campus_sel = st.selectbox("Selecione o Campus:", campi_ifba)
        if st.button("🚪 Sair"):
            st.session_state["autenticado"] = False
            st.rerun()
        st.markdown("---")
        st.caption("🚀 **Desenvolvido por:**")
        st.success("**Thiago Messias Carvalho Soares**")

    # 4. Formulário com Campo de Foto (Arrastar e Soltar)
    with st.form("form_vistoria", clear_on_submit=True):
        st.subheader(f"📝 Nova Vistoria: {campus_sel}")
        c1, c2 = st.columns(2)
        with c1:
            edificacao = st.text_input("Edificação/Bloco:", placeholder="Ex: Pavilhão B...", key="edif")
            disciplina = st.selectbox("Disciplina:", ["Alvenaria", "Estrutura", "Elétrica", "Hidráulica", "Pintura", "Cobertura"], key="disc")
            ambiente = st.text_input("Ambiente/Local:", key="amb")
            descricao = st.text_area("Descrição da Patologia:", key="desc")
            solucoes = st.text_area("Soluções Sugeridas:", key="sol")
            
            # ESPAÇO PARA ARRASTAR FOTOS
            foto_upload = st.file_uploader("📷 Arraste ou selecione a foto da patologia", type=["jpg", "png", "jpeg"])
            
        with c2:
            st.write("**Avaliação GUT**")
            g = st.slider("Gravidade", 1, 5, 3)
            u = st.slider("Urgência", 1, 5, 3)
            t = st.slider("Tendência", 1, 5, 3)
            score = g * u * t
            status = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
            st.metric("Score GUT", score, status)

        if st.form_submit_button("💾 Gravar Registro"):
            if edificacao and descricao and solucoes:
                # Lógica para converter imagem em string para a planilha (opcional)
                foto_data = ""
                if foto_upload:
                    foto_data = "Foto anexada" # Marcador para a planilha
                
                nova_linha = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Campus": campus_sel,
                    "Edificacao": edificacao,
                    "Disciplina": disciplina,
                    "Ambiente": ambiente,
                    "Descricao": descricao,
                    "Solucoes": solucoes,
                    "Foto": foto_data,
                    "Score_GUT": score,
                    "Status": status
                }])
                df_atualizado = pd.concat([df_base, nova_linha], ignore_index=True)
                conn.update(data=df_atualizado)
                st.success("Dados enviados com sucesso!")
                st.rerun()

    # 5. Visualização e PDF
    if not df_base.empty:
        df_filtrado = df_base[df_base['Campus'] == campus_sel]
        if not df_filtrado.empty:
            st.markdown("---")
            st.subheader(f"📋 Registros Atuais - {campus_sel}")
            st.dataframe(df_filtrado.drop(columns=["Campus"]), use_container_width=True)
            
            if st.button("📄 Exportar PDF Assinado"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, f"RELATÓRIO TÉCNICO - {campus_sel.upper()}", ln=True, align='C')
                
                for i, row in df_filtrado.iterrows():
                    pdf.set_font("Arial", 'B', 11)
                    pdf.cell(0, 10, f"Item {i+1}: {row['Edificacao']} | {row['Disciplina']}", ln=True)
                    pdf.set_font("Arial", '', 10)
                    pdf.multi_cell(0, 5, f"Descrição: {row['Descricao']}\nSoluções: {row['Solucoes']}\nPrioridade: {row['Status']}")
                    pdf.ln(5)

                pdf.ln(20)
                pdf.cell(0, 10, "________________________________________________", ln=True, align='C')
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 5, "Thiago Messias Carvalho Soares", ln=True, align='C')
                pdf.cell(0, 5, "Engenheiro Civil - IFBA", ln=True, align='C')
                
                pdf_out = pdf.output(dest='S').encode('latin-1', 'ignore')
                st.download_button("📥 Baixar PDF", data=pdf_out, file_name=f"Vistoria_{campus_sel}.pdf")

    st.markdown("---")
    st.markdown(f"<p style='text-align: center; color: gray;'>🚀 Desenvolvido por <b>Thiago Messias Carvalho Soares</b></p>", unsafe_allow_html=True)
     
