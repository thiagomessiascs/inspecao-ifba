import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inspeção IFBA", layout="wide", page_icon="🏗️")

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
            if usuario == "admin" and senha == "ifba123":
                st.session_state['logado'] = True
                st.rerun()
            else:
                st.sidebar.error("Usuário ou senha incorretos")
        return False
    return True

# --- SISTEMA PRINCIPAL ---
if verificar_login():
    st.sidebar.button("Sair / Logoff", on_click=lambda: st.session_state.update({"logado": False}))
    
    st.title("🏗️ Gestão de Manutenção Predial - IFBA")
    
    # 1. ESCOLHA DO CAMPUS
    campus = st.sidebar.selectbox("Selecione o Campus:", [
        "Salvador", "Feira de Santana", "Vitória da Conquista", 
        "Simões Filho", "Camaçari", "Jequié", "Santo Amaro"
    ])

    # 2. ENTRADA DE DADOS
    with st.expander("➕ Registrar Nova Patologia", expanded=True):
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            disciplina = st.selectbox("Disciplina:", [
                "Alvenaria", "Elétrica", "Hidrossanitário", 
                "Estrutura", "Pavimentação", "Revestimento", 
                "Esquadria", "Cobertura"
            ])
            ambiente = st.text_input("Ambiente/Local:", placeholder="Ex: Sala 04, Bloco B...")
        
        with col2:
            patologia = st.text_input("Patologia Encontrada:")
            solucao = st.text_area("Solução Sugerida:", height=68)

        with col3:
            st.write("**Matriz GUT**")
            g = st.slider("Gravidade", 1, 5, 3)
            u = st.slider("Urgência", 1, 5, 3)
            t = st.slider("Tendência", 1, 5, 3)
            total_gut = g * u * t
            
            # Classificação
            if total_gut >= 100: status = "CRÍTICA"; cor = "🔴"
            elif total_gut >= 50: status = "MÉDIA"; cor = "🟡"
            else: status = "BAIXA"; cor = "🟢"
            
            st.markdown(f"**Prioridade:** {cor} {status} ({total_gut})")

        if st.button("📥 Adicionar na Lista de Inspeção"):
            nova_entrada = {
                "Campus": campus,
                "Disciplina": disciplina,
                "Ambiente": ambiente,
                "Patologia": patologia,
                "GUT": total_gut,
                "Status": status
            }
            st.session_state['inspecoes'].append(nova_entrada)
            st.success("Item adicionado com sucesso!")

    # 3. EXIBIÇÃO E GRÁFICOS
    if st.session_state['inspecoes']:
        df = pd.DataFrame(st.session_state['inspecoes'])
        
        st.divider()
        st.subheader("📊 Resumo da Inspeção Atual")
        
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.dataframe(df, use_container_width=True)
            if st.button("🗑️ Limpar Lista"):
                st.session_state['inspecoes'] = []
                st.rerun()

        with c2:
            fig = px.bar(df, x='Status', title="Patologias por Prioridade",
                         color='Status', color_discrete_map={"CRÍTICA": "red", "MÉDIA": "orange", "BAIXA": "green"})
            st.plotly_express_chart(fig)

    # RODAPÉ
    st.sidebar.markdown("---")
    st.sidebar.caption("🚀 Desenvolvido por:")
    st.sidebar.write("**Thiago Messias Carvalho Soares**")
