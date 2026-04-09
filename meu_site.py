import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Sistema de Inspeção Predial - IFBA", layout="wide")

# 1. Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Carregar dados
try:
    df = conn.read(ttl="0") # ttl="0" força a leitura de dados novos sempre
except Exception as e:
    st.error(f"Erro ao conectar na planilha: {e}")
    df = pd.DataFrame()

# Título e Logo
st.title("🏗️ Sistema de Inspeção Predial - IFBA")
st.markdown("---")

# 3. Sidebar - Filtros e Seleção de Campus
with st.sidebar:
    st.header("Configurações")
    # Lista atualizada de Campi
    campi_ifba = ["Salvador", "Feira de Santana", "Simões Filho", "Santo Amaro", "Vitória da Conquista", "Valença"]
    campus_sel = st.selectbox("Selecione o Campus:", campi_ifba)
    
    if st.button("Sair / Logoff"):
        st.info("Sessão encerrada.")

# 4. Formulário para Nova Patologia
with st.expander("➕ Registrar Nova Patologia", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        disciplina = st.selectbox("Disciplina:", ["Alvenaria", "Estrutura", "Elétrica", "Hidráulica", "Pintura", "Cobertura"])
        ambiente = st.text_input("Ambiente/Local:")
        descricao = st.text_area("Descrição da Patologia:")
        
    with col2:
        gravidade = st.slider("Gravidade", 1, 5, 3)
        urgencia = st.slider("Urgência", 1, 5, 3)
        tendencia = st.slider("Tendência", 1, 5, 3)
        
        # Cálculo de Prioridade (GUT)
        total_gut = gravidade * urgencia * tendencia
        prioridade = "ALTA" if total_gut > 60 else "MÉDIA" if total_gut > 20 else "BAIXA"
        st.write(f"**Prioridade:** {prioridade} ({total_gut})")

    if st.button("💾 Gravar na Planilha"):
        nova_linha = pd.DataFrame([{
            "Data": datetime.now().strftime("%d/%m/%Y"),
            "Campus": campus_sel,
            "Disciplina": disciplina,
            "Ambiente": ambiente,
            "Descricao": descricao,
            "G": gravidade, "U": urgencia, "T": tendencia,
            "Total": total_gut,
            "Prioridade": prioridade
        }])
        
        # Lógica para salvar (Update)
        df_atualizado = pd.concat([df, nova_linha], ignore_index=True)
        conn.update(data=df_atualizado)
        st.success("Dados gravados com sucesso! Clique em 'Clear Cache' se não aparecer abaixo.")

st.markdown("---")

# 5. Visualização e Gráficos
if not df.empty:
    st.subheader(f"Relatório de Inspeções - Campus {campus_sel}")
    
    # Filtrar dados pelo campus selecionado
    df_filtrado = df[df['Campus'] == campus_sel]
    
    if not df_filtrado.empty:
        # Gráfico de Disciplinas
        fig = px.pie(df_filtrado, names='Disciplina', title='Distribuição por Disciplina', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela de Dados
        st.dataframe(df_filtrado, use_container_width=True)
        
        # 6. Gerar PDF
        if st.button("📄 Gerar Relatório PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, f"Relatorio de Inspecao - {campus_sel}", ln=True, align='C')
            
            pdf.set_font("Arial", '', 12)
            pdf.ln(10)
            for index, row in df_filtrado.iterrows():
                pdf.multi_cell(0, 10, f"{row['Data']} - {row['Disciplina']}: {row['Descricao']} (Prioridade: {row['Prioridade']})")
                pdf.ln(2)
            
            pdf_output = pdf.output(dest='S').encode('latin-1', 'ignore')
            st.download_button(label="📥 Baixar PDF", data=pdf_output, file_name=f"relatorio_{campus_sel}.pdf", mime="application/pdf")
    else:
        st.warning(f"Nenhum registro encontrado para o campus {campus_sel}.")
else:
    st.info("Aguardando carregamento de dados da planilha...")
    
