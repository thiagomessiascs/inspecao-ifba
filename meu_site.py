import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide")

# 1. Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Carregar dados
try:
    df_base = conn.read(ttl="0") 
except Exception as e:
    st.error(f"Erro ao conectar na planilha: {e}")
    df_base = pd.DataFrame()

# Título ajustado conforme solicitado
st.title("🏗️ Inspeção Predial IFBA")
st.markdown("---")

# 3. Sidebar - Configurações e Lista Completa de Campi
with st.sidebar:
    st.header("Configurações")
    # Lista de todos os campi do IFBA
    campi_ifba = [
        "Salvador", "Feira de Santana", "Simões Filho", "Santo Amaro", 
        "Vitória da Conquista", "Valença", "Porto Seguro", "Eunápolis", 
        "Camaçari", "Paulo Afonso", "Jacobina", "Irecê", "Brumado", 
        "Jequié", "Seabra", "Ilhéus", "Itabuna", "Barreiras", "Juazeiro"
    ]
    campus_sel = st.selectbox("Selecione o Campus:", sorted(campi_ifba))
    
    if st.button("Sair / Logoff"):
        st.info("Sessão encerrada.")

# 4. Formulário de Registro com campo de Edificação
# O 'key' no final de cada campo ajuda a limpar os dados depois
with st.form("form_inspecao", clear_on_submit=True):
    st.subheader("➕ Registrar Nova Patologia")
    col1, col2 = st.columns(2)
    
    with col1:
        edificacao = st.text_input("Edificação Avaliada:", placeholder="Ex: Ginásio, Pav. de Aulas...", key="edif")
        disciplina = st.selectbox("Disciplina:", ["Alvenaria", "Estrutura", "Elétrica", "Hidráulica", "Pintura", "Cobertura"], key="disc")
        ambiente = st.text_input("Ambiente/Local Específico:", key="amb")
        descricao = st.text_area("Descrição da Patologia:", key="desc")
        
    with col2:
        gravidade = st.slider("Gravidade", 1, 5, 3, key="g")
        urgencia = st.slider("Urgência", 1, 5, 3, key="u")
        tendencia = st.slider("Tendência", 1, 5, 3, key="t")
        
        # Cálculo GUT
        total_gut = gravidade * urgencia * tendencia
        prioridade = "CRÍTICA" if total_gut > 60 else "MÉDIA" if total_gut > 20 else "BAIXA"
        st.write(f"**Prioridade Calculada:** {prioridade} ({total_gut})")

    # Botão de submissão do formulário
    enviado = st.form_submit_button("💾 Gravar na Planilha")
    
    if enviado:
        if edificacao and descricao:
            nova_linha = pd.DataFrame([{
                "Data": datetime.now().strftime("%d/%m/%Y"),
                "Campus": campus_sel,
                "Edificacao": edificacao,
                "Disciplina": disciplina,
                "Ambiente": ambiente,
                "Descricao": descricao,
                "Total": total_gut,
                "Prioridade": prioridade
            }])
            
            df_atualizado = pd.concat([df_base, nova_linha], ignore_index=True)
            conn.update(data=df_atualizado)
            st.success("Registro adicionado! Campos limpos para a próxima inserção.")
            st.rerun() # Atualiza a tela para limpar visualmente e carregar a tabela nova
        else:
            st.warning("Por favor, preencha a Edificação e a Descrição.")

st.markdown("---")

# 5. Relatórios Filtrados (Garante que não misture os campi)
if not df_base.empty:
    # Filtro rigoroso por Campus selecionado
    df_filtrado = df_base[df_base['Campus'] == campus_sel]
    
    if not df_filtrado.empty:
        st.subheader(f"📋 Itens Registrados: {campus_sel}")
        
        # Mostra apenas as colunas relevantes para o relatório local
        st.dataframe(df_filtrado.drop(columns=["Campus"]), use_container_width=True)
        
        # Gráfico de Prioridades
        fig = px.bar(df_filtrado, x='Prioridade', title=f"Resumo de Prioridades - {campus_sel}", 
                     color='Prioridade', color_discrete_map={"CRÍTICA": "red", "MÉDIA": "orange", "BAIXA": "green"})
        st.plotly_chart(fig, use_container_width=True)
        
        # 6. Botão para Gerar PDF
        if st.button("📄 Gerar Relatório PDF da Vistoria"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, f"Relatorio de Inspecao Predial - IFBA {campus_sel}", ln=True, align='C')
            
            pdf.set_font("Arial", '', 10)
            pdf.ln(10)
            for i, row in df_filtrado.iterrows():
                text = f"Item {i+1}: {row['Edificacao']} | {row['Disciplina']} | Local: {row['Ambiente']}\nDescricao: {row['Descricao']}\nPrioridade: {row['Prioridade']} ({row['Total']})\n"
                pdf.multi_cell(0, 8, text)
                pdf.ln(4)
                pdf.cell(0, 0, "", "T") # Linha divisória
                pdf.ln(4)
            
            pdf_out = pdf.output(dest='S').encode('latin-1', 'ignore')
            st.download_button(label="📥 Baixar PDF", data=pdf_out, file_name=f"Vistoria_{campus_sel}.pdf", mime="application/pdf")
    else:
        st.info(f"Nenhum registro encontrado para o campus {campus_sel}.")
