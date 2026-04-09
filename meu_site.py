import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inspeção IFBA", layout="wide", page_icon="🏗️")

# --- FUNÇÃO DE LOGIN ---
def verificar_login():
    if 'logado' not in st.session_state:
        st.session_state['logado'] = False

    if not st.session_state['logado']:
        st.sidebar.title("🔐 Acesso ao Sistema")
        usuario = st.sidebar.text_input("Usuário")
        senha = st.sidebar.text_input("Senha", type="password")
        
        if st.sidebar.button("Entrar"):
            # Aqui você define seu usuário e senha
            if usuario == "admin" and senha == "ifba123":
                st.session_state['logado'] = True
                st.rerun()
            else:
                st.sidebar.error("Usuário ou senha incorretos")
        return False
    return True

# --- RODAPÉ DE CRÉDITOS ---
def adicionar_rodape():
    st.sidebar.markdown("---")
    st.sidebar.caption("🚀 **Desenvolvido por:**")
    st.sidebar.write("Thiago Messias Carvalho Soares")

# --- EXECUÇÃO DO SISTEMA ---
if verificar_login():
    # Menu Lateral - Logout e Seleção
    if st.sidebar.button("Sair / Logoff"):
        st.session_state['logado'] = False
        st.rerun()

    st.sidebar.header("📍 Localização")
    predio = st.sidebar.selectbox("Selecione o Prédio:", 
                                 ["Usina de Biodiesel", "Ginásio", "Pavilhão de Aulas", "Administrativo"])

    # Cabeçalho Principal
    st.title("🏗️ Sistema de Inspeção Predial - IFBA")
    st.subheader(f"Edificação: {predio}")

    # Abas por Disciplina
    tab1, tab2, tab3 = st.tabs(["ALVENARIA", "ELÉTRICA", "HIDROSSANITÁRIO"])

    with tab1:
        st.markdown("### 🧱 Checklist de Alvenaria")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            patologia = st.selectbox("Patologia/Item a Verificar:", [
                "Fissuras ou trincas em paredes", 
                "Eflorescência (manchas brancas)", 
                "Desplacamento de reboco",
                "Umidade ascendente"
            ])
            solucao = st.text_area("Solução Recomendada", placeholder="Descreva a intervenção necessária...")

        with col2:
            st.write("**Matriz GUT (Prioridade)**")
            g = st.select_slider("Gravidade (G)", options=[1,2,3,4,5], key="g1")
            u = st.select_slider("Urgência (U)", options=[1,2,3,4,5], key="u1")
            t = st.select_slider("Tendência (T)", options=[1,2,3,4,5], key="t1")
            
            resultado = g * u * t
            
            if resultado >= 100:
                st.error(f"GUT: {resultado} - CRÍTICA")
            elif resultado >= 50:
                st.warning(f"GUT: {resultado} - MÉDIA")
            else:
                st.success(f"GUT: {resultado} - BAIXA")

    if st.button("💾 Gravar Inspeção"):
        st.balloons()
        st.success(f"Dados da unidade '{predio}' registrados com sucesso!")

# Adiciona seu nome no final do menu lateral independente da tela
adicionar_rodape()