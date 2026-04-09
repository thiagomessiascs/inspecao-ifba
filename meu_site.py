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
        st.set_page_config(page_title="Acesso Restrito - IFBA", page_icon="🔐")
        st.title("🔐 Inspeção Predial IFBA")
        st.subheader("Controle de Acesso")
        
        senha = st.text_input("Digite a senha para acessar o sistema:", type="password")
        if st.button("Entrar"):
            # Senha padrão para o sistema
            if senha == "IFBA2026":
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta! Entre em contato com a administração.")
        return False
    return True

# Início do Sistema
if verificar_senha():
    st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide", page_icon="🏗️")

    # 2. Conexão com Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)

    # 3. Carregar dados
    try:
        df_base = conn.read(ttl="0")
    except Exception as e:
        st.error(f"Erro na conexão com a planilha: {e}")
        df_base = pd.DataFrame()

    st.title("🏗️ Inspeção Predial IFBA")
    st.markdown("---")

    # 4. Sidebar - Filtros e Logout
    with st.sidebar:
        st.header("⚙️ Configurações")
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

    # 5. Formulário de Registro (Limpa ao enviar)
    with st.form("form_inspecao", clear_on_submit=True):
        st.subheader(f"➕ Nova Vistoria - {campus_sel}")
        col1, col2 = st.columns(2)
        
        with col1:
            edificacao = st.text_input("Edificação/Bloco:", placeholder="Ex: Ginásio, Pav. de Aulas...", key="edif")
            disciplina = st.selectbox("Disciplina:", ["Alvenaria", "Estrutura", "Elétrica", "Hidráulica", "Pintura", "Cobertura", "Drenagem"], key="disc")
            ambiente = st.text_input("Ambiente/Local Específico:", key="amb")
            descricao = st.text_area("Descrição da Patologia:", key="desc")
            
        with col2:
            st.write("**Avaliação GUT**")
            gravidade = st.slider("Gravidade", 1, 5, 3, key="g")
            urgencia = st.slider("Urgência", 1, 5, 3, key="u")
            tendencia = st.slider("Tendência", 1, 5, 3, key="t")
            
            total_gut = gravidade * urgencia * tendencia
            prioridade = "CRÍTICA" if total_gut > 60 else "MÉDIA" if total_gut > 20 else "BAIXA"
            st.info(f"Prioridade: {prioridade} (Score: {total_gut})")

        enviado = st.form_submit_button("💾 Salvar na Planilha")
        
        if enviado:
            if edificacao and descricao:
                nova_linha = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Campus": campus_sel,
                    "Edificacao": edificacao,
                    "Disciplina": disciplina,
                    "Ambiente": ambiente,
                    "Descricao": descricao,
                    "Score_GUT": total_gut,
                    "Status": prioridade
                }])
                df_atualizado = pd.concat([df_base, nova_linha], ignore_index=True)
                conn.update(data=df_atualizado)
                st.success("Registro salvo!")
                st.rerun()

    st.markdown("---")

    # 6. Exibição e Relatório PDF
    if not df_base.empty:
        df_filtrado = df_base[df_base['Campus'] == campus_sel]
        
        if not df_filtrado.empty:
            st.subheader(f"📋 Registros: {campus_sel}")
            st.dataframe(df_filtrado.drop(columns=["Campus"]), use_container_width=True)
            
            # Gráfico
            fig = px.bar(df_filtrado, x='Status', title="Criticidade das Patologias",
                         color='Status', color_discrete_map={"CRÍTICA": "red", "MÉDIA": "orange", "BAIXA": "green"})
            st.plotly_chart(fig, use_container_width=True)
            
            # 7. Geração de PDF com ASSINATURA
            if st.button("📄 Gerar PDF com Assinatura"):
                pdf = FPDF()
                pdf.add_page()
                
                # Cabeçalho
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, f"RELATORIO DE INSPECAO PREDIAL - {campus_sel.upper()}", ln=True, align='C')
                pdf.set_font("Arial", 'I', 10)
                pdf.cell(200, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
                
                pdf.ln(10)
                pdf.set_font("Arial", '', 10)
                
                # Conteúdo
                for i, row in df_filtrado.iterrows():
                    pdf.set_font("Arial", 'B', 11)
                    pdf.cell(0, 8, f"Item {i+1}: {row['Edificacao']} - {row['Disciplina']}", ln=True)
                    pdf.set_font("Arial", '', 10)
                    pdf.multi_cell(0, 6, f"Local: {row['Ambiente']}\nDescricao: {row['Descricao']}\nPrioridade: {row['Status']} (GUT: {row['Score_GUT']})")
                    pdf.ln(2)
                    pdf.cell(190, 0, "", "T")
                    pdf.ln(4)

                # ESPAÇO PARA ASSINATURA
                pdf.ln(20)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 10, "________________________________________________", ln=True, align='C')
                # Aqui inserimos seus dados profissionais automaticamente
                pdf.cell(0, 5, "Thiago Messias", ln=True, align='C') 
                pdf.set_font("Arial", '', 9)
                pdf.cell(0, 5, "Engenheiro Civil - IFBA", ln=True, align='C')
                
                pdf_out = pdf.output(dest='S').encode('latin-1', 'ignore')
                st.download_button(label="📥 Baixar PDF Assinado", data=pdf_out, file_name=f"Inspecao_{campus_sel}.pdf", mime="application/pdf")
        else:
            st.info(f"Sem registros para {campus_sel}.")
