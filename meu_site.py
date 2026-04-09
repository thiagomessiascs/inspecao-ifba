import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide", page_icon="🏗️")

# --- INICIALIZAÇÃO DO BANCO DE DADOS TEMPORÁRIO ---
if 'inspecoes' not in st.session_state:
    st.session_state['inspecoes'] = []

# --- FUNÇÃO DE LOGIN ---
def verificar_login():
    if 'logado' not in st.session_state:
        st.session_state['logado'] = False
    if not st.session_state['logado']:
        st.sidebar.title("🔐 Acesso")
        usuario = st.sidebar.text_input("Usuário")
        senha = st.sidebar.text_input("Senha", type="password")
        if st.sidebar.button("Entrar"):
            if usuario.lower() == "admin" and senha == "ifba123":
                st.session_state['logado'] = True
                st.rerun()
            else:
                st.sidebar.error("Usuário ou senha incorretos")
        return False
    return True

# --- FUNÇÃO PARA GERAR PDF ---
def gerar_pdf(df, campus, edificacao):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, u"Inspeção Predial - IFBA", ln=True, align='C')
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, f"Campus: {campus} | Edificacao: {edificacao}", ln=True, align='C')
    pdf.ln(10)
    
    # Cabeçalho da Tabela
    pdf.set_font("Arial", "B", 10)
    pdf.cell(35, 10, "Disciplina", 1)
    pdf.cell(35, 10, "Ambiente", 1)
    pdf.cell(80, 10, "Patologia", 1)
    pdf.cell(20, 10, "GUT", 1)
    pdf.cell(20, 10, "Status", 1)
    pdf.ln()
    
    # Dados
    pdf.set_font("Arial", "", 9)
    for index, row in df.iterrows():
        pdf.cell(35, 10, str(row['Disciplina']), 1)
        pdf.cell(35, 10, str(row['Ambiente']), 1)
        pdf.cell(80, 10, str(row['Patologia'])[:45], 1)
        pdf.cell(20, 10, str(row['GUT']), 1)
        pdf.cell(20, 10, str(row['Status']), 1)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

# --- SISTEMA PRINCIPAL ---
if verificar_login():
    st.sidebar.button("Sair / Logoff", on_click=lambda: st.session_state.update({"logado": False}))
    
    st.title("🏗️ Inspeção Predial IFBA")
    
    # 1. IDENTIFICAÇÃO (SIDEBAR) - LISTA COMPLETA DOS CAMPI
    st.sidebar.header("📍 Localização")
    lista_campi = [
        "Barreiras", "Brumado", "Camaçari", "Euclides da Cunha", "Feira de Santana", 
        "Ilhéus", "Irecê", "Jacobina", "Jequié", "Juazeiro", "Lauro de Freitas", 
        "Paulo Afonso", "Porto Seguro", "Salvador", "Santo Amaro", "Santo Antônio de Jesus", 
        "Seabra", "Simões Filho", "Ubaitaba", "Valença", "Vitória da Conquista"
    ]
    campus_sel = st.sidebar.selectbox("Campus:", lista_campi)
    edificacao_sel = st.sidebar.text_input("Edificação:", placeholder="Ex: Ginásio, Pav. de Aulas...")

    # 2. ENTRADA DE DADOS
    with st.expander("➕ Registrar Novo Item de Inspeção", expanded=True):
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            disciplina = st.selectbox("Disciplina:", ["Alvenaria", "Elétrica", "Hidrossanitário", "Estrutura", "Pavimentação", "Revestimento", "Esquadria", "Cobertura"], key="disc_input")
            ambiente = st.text_input("Ambiente/Local:", placeholder="Ex: Sala 01...", key="amb_input")
        
        with col2:
            patologia = st.text_input("Patologia:", key="pato_input")
            solucao = st.text_area("Solução Sugerida:", height=68, key="sol_input")

        with col3:
            st.write("**Matriz GUT**")
            g = st.slider("Gravidade", 1, 5, 3, key="g_input")
            u = st.slider("Urgência", 1, 5, 3, key="u_input")
            t = st.slider("Tendência", 1, 5, 3, key="t_input")
            total_gut = g * u * t
            
            if total_gut >= 100: status = "CRÍTICA"; cor = "🔴"
            elif total_gut >= 50: status = "MÉDIA"; cor = "🟡"
            else: status = "BAIXA"; cor = "🟢"
            
            st.markdown(f"**Prioridade:** {cor} {status} ({total_gut})")

        # FUNÇÃO PARA ADICIONAR E LIMPAR OS CAMPOS
        def adicionar_item():
            if edificacao_sel and st.session_state.amb_input and st.session_state.pato_input:
                nova_entrada = {
                    "Disciplina": st.session_state.disc_input, 
                    "Ambiente": st.session_state.amb_input, 
                    "Patologia": st.session_state.pato_input, 
                    "GUT": total_gut, 
                    "Status": status
                }
                st.session_state['inspecoes'].append(nova_entrada)
                # Limpa os campos após adicionar
                st.session_state.amb_input = ""
                st.session_state.pato_input = ""
                st.session_state.sol_input = ""
                st.success("Registro adicionado com sucesso!")
            else:
                st.error("Por favor, preencha a Edificação, Ambiente e Patologia!")

        st.button("📥 Adicionar na Lista", on_click=adicionar_item)

    # 3. EXIBIÇÃO E PDF
    if st.session_state['inspecoes']:
        df = pd.DataFrame(st.session_state['inspecoes'])
        st.divider()
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader(f"📋 Itens: {edificacao_sel}")
            st.dataframe(df, use_container_width=True)
            
            pdf_bytes = gerar_pdf(df, campus_sel, edificacao_sel)
            st.download_button(label="📥 Baixar Relatório em PDF", data=pdf_bytes, file_name=f"Vistoria_{campus_sel}_{edificacao_sel}.pdf", mime="application/pdf")
            
            if st.button("🗑️ Limpar Tudo"):
                st.session_state['inspecoes'] = []
                st.rerun()

        with c2:
            st.subheader("📊 Prioridades")
            fig = px.bar(df, x='Status', color='Status', color_discrete_map={"CRÍTICA": "red", "MÉDIA": "orange", "BAIXA": "green"})
            st.plotly_chart(fig, use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.caption("🚀 Desenvolvido por: Thiago Messias Carvalho Soares")
