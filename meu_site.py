import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from datetime import datetime

# 1. Sistema de Autenticação (Login)
def verificar_senha():
    # Inicializa o estado de autenticação se não existir
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    # Se não estiver autenticado, mostra a tela de login
    if not st.session_state["autenticado"]:
        st.set_page_config(page_title="Login - Inspeção IFBA", page_icon="🔐")
        
        # Centralizando o formulário de login
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔐 Acesso Restrito")
            st.subheader("Inspeção Predial IFBA")
            
            senha = st.text_input("Digite a senha de acesso:", type="password")
            if st.button("Entrar"):
                if senha == "IFBA2026": # <-- SENHA DEFINIDA AQUI
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
        return False
    return True

# O sistema só carrega se a senha estiver correta
if verificar_senha():
    st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide", page_icon="🏗️")

    # 2. Conexão com Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)

    # 3. Carregar dados atualizados
    try:
        df_base = conn.read(ttl="0")
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
        df_base = pd.DataFrame()

    st.title("🏗️ Sistema de Inspeção Predial - IFBA")
    st.markdown("---")

    # 4. Sidebar - Filtros, Lista de Campi e Logout
    with st.sidebar:
        st.header("⚙️ Painel de Controle")
        
        campi_ifba = sorted([
            "Salvador", "Feira de Santana", "Simões Filho", "Santo Amaro", 
            "Vitória da Conquista", "Valença", "Porto Seguro", "Eunápolis", 
            "Camaçari", "Paulo Afonso", "Jacobina", "Irecê", "Brumado", 
            "Jequié", "Seabra", "Ilhéus", "Itabuna", "Barreiras", "Juazeiro"
        ])
        campus_sel = st.selectbox("Selecione o Campus para trabalhar:", campi_ifba)
        
        st.markdown("---")
        if st.button("🚪 Sair do Sistema"):
            st.session_state["autenticado"] = False
            st.rerun()

    # 5. Formulário de Registro (Limpa campos ao salvar)
    with st.form("form_registro", clear_on_submit=True):
        st.subheader(f"📝 Novo Registro: {campus_sel}")
        col1, col2 = st.columns(2)
        
        with col1:
            edificacao = st.text_input("Edificação Avaliada:", placeholder="Ex: Ginásio, Pavilhão A...", key="edif")
            disciplina = st.selectbox("Disciplina:", ["Alvenaria", "Estrutura", "Elétrica", "Hidráulica", "Pintura", "Cobertura", "Drenagem"], key="disc")
            ambiente = st.text_input("Localização/Ambiente:", key="amb")
            descricao = st.text_area("Descrição da Patologia:", key="desc")
            
        with col2:
            st.write("**Avaliação de Prioridade (GUT)**")
            gravidade = st.slider("Gravidade (1 a 5)", 1, 5, 3, key="g")
            urgencia = st.slider("Urgência (1 a 5)", 1, 5, 3, key="u")
            tendencia = st.slider("Tendência (1 a 5)", 1, 5, 3, key="t")
            
            score = gravidade * urgencia * tendencia
            status = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
            st.info(f"Classificação: {status} (Score: {score})")

        if st.form_submit_button("💾 Salvar Registro"):
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
                st.success("Dados enviados com sucesso!")
                st.rerun()
            else:
                st.warning("Preencha todos os campos obrigatórios.")

    st.markdown("---")

    # 6. Exibição dos Dados Filtrados
    if not df_base.empty:
        # Garante que não mistura registros de campi diferentes
        df_filtrado = df_base[df_base['Campus'] == campus_sel]
        
        if not df_filtrado.empty:
            st.subheader(f"📋 Relatório de Itens - {campus_sel}")
            st.dataframe(df_filtrado.drop(columns=["Campus"]), use_container_width=True)
            
            # Gráfico de Criticidade
            fig = px.pie(df_filtrado, names='Status', title="Distribuição de Criticidade",
                         color='Status', color_discrete_map={"CRÍTICA": "red", "MÉDIA": "orange", "BAIXA": "green"})
            st.plotly_chart(fig, use_container_width=True)
            
            # 7. Gerar PDF com Assinatura Técnica
            if st.button("📄 Gerar Relatório PDF"):
                pdf = FPDF()
                pdf.add_page()
                
                # Cabeçalho do PDF
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, f"RELATÓRIO TÉCNICO DE INSPEÇÃO - {campus_sel.upper()}", ln=True, align='C')
                pdf.set_font("Arial", 'I', 10)
                pdf.cell(200, 10, f"Data do Relatório: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
                pdf.ln(10)
                
                # Listagem das patologias
                for i, row in df_filtrado.iterrows():
                    pdf.set_font("Arial", 'B', 11)
                    pdf.cell(0, 8, f"Item {i+1}: {row['Edificacao']} | {row['Disciplina']}", ln=True)
                    pdf.set_font("Arial", '', 10)
                    pdf.multi_cell(0, 6, f"Local: {row['Ambiente']}\nDescrição: {row['Descricao']}\nPrioridade: {row['Status']} (Score: {row['Score_GUT']})")
                    pdf.ln(2)
                    pdf.cell(190, 0, "", "T")
                    pdf.ln(4)

                # Seção de Assinatura Profissional
                pdf.ln(20)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 10, "________________________________________________", ln=True, align='C')
                pdf.cell(0, 5, "Thiago Messias", ln=True, align='C') # Seu Nome
                pdf.set_font("Arial", '', 9)
                pdf.cell(0, 5, "Engenheiro Civil - IFBA", ln=True, align='C') # Seu Cargo
                
                pdf_out = pdf.output(dest='S').encode('latin-1', 'ignore')
                st.download_button(label="📥 Baixar PDF Assinado", data=pdf_out, file_name=f"Inspecao_{campus_sel}.pdf", mime="application/pdf")
        else:
            st.info(f"Não há registros de inspeção para o campus {campus_sel}.")
