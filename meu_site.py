import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from datetime import datetime

# 1. Sistema de Autenticação (Login)
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
                if senha == "IFBA2026": # Sua senha definida
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
        return False
    return True

if verificar_senha():
    st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide", page_icon="🏗️")

    # --- CABEÇALHO PERSONALIZADO COM LOGO CIRCULAR ---
    # URL da logo oficial e Estilização
    url_logo_ifba = "https://portal.ifba.edu.br/proen/imagens/marcas-if/marcas-ifba-v/ifba-vertical.png"
    
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 10px solid #2e7d32; margin-bottom: 25px;">
            <img src="{url_logo_ifba}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: contain; background: white; padding: 5px; border: 2px solid #2e7d32;">
            <div style="margin-left: 20px;">
                <h1 style="margin: 0; color: #1e4620; font-family: sans-serif;">Inspeção Predial IFBA</h1>
                <p style="margin: 0; color: #666;">Engenharia e Manutenção</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Conexão com Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df_base = conn.read(ttl="0")
    except Exception as e:
        st.error(f"Erro na planilha: {e}")
        df_base = pd.DataFrame()

    # 3. Sidebar (Painel Lateral)
    with st.sidebar:
        st.header("🏢 Unidades IFBA")
        campi_ifba = sorted([
            "Salvador", "Feira de Santana", "Simões Filho", "Santo Amaro", 
            "Vitória da Conquista", "Valença", "Porto Seguro", "Eunápolis", 
            "Camaçari", "Paulo Afonso", "Jacobina", "Irecê", "Brumado", 
            "Jequié", "Seabra", "Ilhéus", "Itabuna", "Barreiras", "Juazeiro"
        ])
        campus_sel = st.selectbox("Selecione o Campus:", campi_ifba)
        
        st.markdown("---")
        if st.button("🚪 Sair do Sistema"):
            st.session_state["autenticado"] = False
            st.rerun()
            
        # ASSINATURA NO RODAPÉ DA SIDEBAR
        st.write("")
        st.write("")
        st.markdown("---")
        st.caption("🚀 **Desenvolvido por:**")
        st.success("**Thiago Messias Carvalho Soares**")

    # 4. Formulário de Registro (Limpa após salvar)
    with st.form("form_inspecao", clear_on_submit=True):
        st.subheader(f"📝 Nova Vistoria: {campus_sel}")
        c1, c2 = st.columns(2)
        with c1:
            edificacao = st.text_input("Edificação/Bloco:", placeholder="Ex: Ginásio...", key="edif")
            disciplina = st.selectbox("Disciplina:", ["Alvenaria", "Estrutura", "Elétrica", "Hidráulica", "Pintura", "Cobertura", "Drenagem"], key="disc")
            ambiente = st.text_input("Ambiente/Local:", key="amb")
            descricao = st.text_area("Descrição da Patologia:", key="desc")
        with c2:
            st.write("**Avaliação GUT**")
            g = st.slider("Gravidade", 1, 5, 3, key="g")
            u = st.slider("Urgência", 1, 5, 3, key="u")
            t = st.slider("Tendência", 1, 5, 3, key="t")
            score = g * u * t
            status = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
            st.metric("Score GUT", score, status)

        if st.form_submit_button("💾 Gravar na Planilha"):
            if edificacao and descricao:
                nova_linha = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Campus": campus_sel,
                    "Edificacao": edificacao,
                    "Disciplina": disciplina,
                    "Ambiente": ambiente,
                    "Descricao": descricao,
                    "Score_GUT": score,
                    "Status": status
                }])
                df_atualizado = pd.concat([df_base, nova_linha], ignore_index=True)
                conn.update(data=df_atualizado)
                st.success("Registro adicionado com sucesso!")
                st.rerun()

    # 5. Listagem de Dados (Isolada por Campus)
    if not df_base.empty:
        df_filtrado = df_base[df_base['Campus'] == campus_sel]
        if not df_filtrado.empty:
            st.markdown("---")
            st.subheader(f"📋 Registros Atuais - {campus_sel}")
            st.dataframe(df_filtrado.drop(columns=["Campus"]), use_container_width=True)
            
            # 6. Gerar PDF com Assinatura Técnica
            if st.button("📄 Exportar PDF Assinado"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, f"RELATÓRIO DE VISTORIA - {campus_sel.upper()}", ln=True, align='C')
                pdf.set_font("Arial", 'I', 10)
                pdf.cell(200, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
                pdf.ln(10)

                for i, row in df_filtrado.iterrows():
                    pdf.set_font("Arial", 'B', 11)
                    pdf.cell(0, 8, f"Item {i+1}: {row['Edificacao']} | {row['Disciplina']}", ln=True)
                    pdf.set_font("Arial", '', 10)
                    pdf.multi_cell(0, 6, f"Ambiente: {row['Ambiente']}\nDescrição: {row['Descricao']}\nStatus: {row['Status']} (Score: {row['Score_GUT']})")
                    pdf.ln(2)
                    pdf.cell(190, 0, "", "T")
                    pdf.ln(4)

                # Assinatura Final no PDF
                pdf.ln(20)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 10, "________________________________________________", ln=True, align='C')
                pdf.cell(0, 5, "Thiago Messias Carvalho Soares", ln=True, align='C')
                pdf.set_font("Arial", '', 9)
                pdf.cell(0, 5, "Engenheiro Civil - IFBA", ln=True, align='C')
                
                pdf_out = pdf.output(dest='S').encode('latin-1', 'ignore')
                st.download_button(label="📥 Baixar PDF do Relatório", data=pdf_out, file_name=f"Vistoria_{campus_sel}.pdf", mime="application/pdf")
        else:
            st.info(f"Sem vistorias registradas para {campus_sel} até o momento.")

    # Rodapé fixo na página
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: gray;'>Desenvolvido por <b>Thiago Messias Carvalho Soares</b></p>", unsafe_allow_html=True)
