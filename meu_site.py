import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import tempfile
import os

# 1. Autenticação
def verificar_senha():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if not st.session_state["autenticado"]:
        st.set_page_config(page_title="Login - Inspeção IFBA", page_icon="🔐")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔐 Acesso Restrito")
            senha = st.text_input("Senha:", type="password")
            if st.button("Entrar"):
                if senha == "IFBA2026":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
        return False
    return True

if verificar_senha():
    st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide")

    # --- Cabeçalho do Site ---
    st.markdown("""
        <div style="background-color: #fcfcfc; padding: 20px; border-radius: 15px; border-left: 10px solid #2e7d32; margin-bottom: 25px;">
            <h1 style="margin: 0; color: #1e4620;">Sistema de Inspeção Predial - IFBA</h1>
            <p style="margin: 0; color: #666;">Engenharia, Manutenção e Vistorias Técnicas</p>
        </div>
    """, unsafe_allow_html=True)

    # Conexão GSheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(ttl="0")

    # Sidebar
    with st.sidebar:
        st.header("🏢 Unidades IFBA")
        lista_campi = sorted(["Salvador", "Jacobina", "Barreiras", "Feira de Santana", "Simões Filho", "Santo Amaro", "Irecê", "Jequié"])
        campus_sel = st.selectbox("Selecione o Campus:", lista_campi)
        
        if "foto_pdf" not in st.session_state:
            st.session_state["foto_pdf"] = None

    # Formulário
    with st.form("form_vistoria"):
        st.subheader(f"📝 Nova Vistoria: {campus_sel}")
        c1, c2 = st.columns(2)
        with c1:
            edificacao = st.text_input("Edificação/Bloco:")
            disciplina = st.selectbox("Disciplina:", ["Alvenaria", "Estrutura", "Elétrica", "Hidráulica", "Pintura", "Cobertura"])
            ambiente = st.text_input("Local/Ambiente:")
            descricao = st.text_area("Descrição da Patologia:")
            solucoes = st.text_area("Soluções Sugeridas:")
        with c2:
            st.write("**📸 Evidência Fotográfica**")
            arquivo_foto = st.file_uploader("Upload da foto", type=["jpg", "png", "jpeg"])
            if arquivo_foto:
                img = Image.open(arquivo_foto)
                st.session_state["foto_pdf"] = img
                st.image(img, use_container_width=True)
            
            g = st.slider("Gravidade", 1, 5, 3)
            u = st.slider("Urgência", 1, 5, 3)
            t = st.slider("Tendência", 1, 5, 3)
            score = g * u * t
            status = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
            st.metric("Prioridade", status, f"Score: {score}")

        if st.form_submit_button("💾 Salvar Inspeção"):
            st.success("Registro salvo na base de dados!")

    # --- Gerador de PDF ---
    if not df_base.empty:
        df_filtrado = df_base[df_base['Campus'] == campus_sel]
        
        def gerar_pdf(dados, foto_pil):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, f"RELATÓRIO DE INSPEÇÃO - IFBA {campus_sel.upper()}", ln=True, align='C')
            pdf.ln(5)

            for i, row in dados.iterrows():
                # Título do Item com fundo cinza claro (substituindo o preto)
                pdf.set_font("Arial", 'B', 11)
                pdf.set_fill_color(240, 240, 240)
                pdf.cell(190, 8, f"ITEM {i+1}: {row['Edificacao']} - {row['Disciplina']}", ln=True, fill=True)
                
                y_topo = pdf.get_y()
                
                # Coluna da Esquerda: Dados
                pdf.set_font("Arial", 'B', 10)
                pdf.ln(2)
                pdf.cell(115, 6, f"Ambiente: {row['Ambiente']}", ln=True)
                pdf.set_font("Arial", '', 10)
                pdf.multi_cell(115, 5, f"Descrição: {row['Descricao']}")
                pdf.multi_cell(115, 5, f"Solução: {row['Solucoes']}")
                
                # Status Colorido
                pdf.set_font("Arial", 'B', 10)
                cor_status = (211, 47, 47) if row['Status'] == "CRÍTICA" else (218, 165, 32)
                pdf.set_text_color(*cor_status)
                pdf.cell(115, 8, f"PRIORIDADE: {row['Status']} (GUT: {row['Score_GUT']})", ln=True)
                pdf.set_text_color(0, 0, 0)

                # Coluna da Direita: Imagem
                if foto_pil:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                        foto_pil.convert("RGB").save(tmp.name)
                        pdf.image(tmp.name, x=135, y=y_topo + 5, w=55)
                        tmp_path = tmp.name
                    if os.path.exists(tmp_path): os.remove(tmp_path)
                
                pdf.set_y(max(pdf.get_y(), y_topo + 45))
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(4)

            # Rodapé do PDF
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(190, 5, "________________________________________________", ln=True, align='C')
            pdf.cell(190, 5, "Thiago Messias Carvalho Soares", ln=True, align='C')
            pdf.cell(190, 5, "Engenheiro Civil - IFBA", ln=True, align='C')
            
            return pdf.output(dest='S').encode('latin-1', 'ignore')

        if st.session_state["foto_pdf"] is not None:
            btn_pdf = gerar_pdf(df_filtrado, st.session_state["foto_pdf"])
            st.download_button(
                label="📄 Baixar Relatório PDF com Fotos",
                data=btn_pdf,
                file_name=f"Relatorio_{campus_sel}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
