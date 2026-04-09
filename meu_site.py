import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide")
st.title("🏗️ Sistema de Inspeção Predial - IFBA")

# Criando a conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOGIN SIMPLES ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.sidebar.title("🔐 Acesso")
    u = st.sidebar.text_input("Usuário")
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u == "admin" and p == "ifba123":
            st.session_state.logado = True
            st.rerun()
else:
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.button("Sair / Logoff", on_click=lambda: st.session_state.update({"logado": False}))
    lista_campi = ["Salvador", "Feira de Santana", "Simões Filho", "Santo Amaro", "Vitória da Conquista"]
    campus_sel = st.sidebar.selectbox("Selecione o Campus:", lista_campi)
    edificacao_sel = st.sidebar.text_input("Edificação:", placeholder="Ex: Pavilhão A")

    # --- LEITURA DOS DADOS ---
    try:
        # Lê a planilha em tempo real
        df_base = conn.read(ttl=0)
    except:
        # Se a planilha estiver vazia, cria a estrutura
        df_base = pd.DataFrame(columns=["Campus", "Edificacao", "Disciplina", "Ambiente", "Patologia", "GUT", "Status"])

    # --- FORMULÁRIO DE ENTRADA ---
    with st.expander("➕ Registrar Nova Patologia", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            disciplina = st.selectbox("Disciplina:", ["Alvenaria", "Elétrica", "Hidrossanitário", "Estrutura", "Cobertura"])
            ambiente = st.text_input("Ambiente/Local:")
            patologia = st.text_input("Descrição da Patologia:")
        with col2:
            g = st.slider("Gravidade", 1, 5, 3)
            u = st.slider("Urgência", 1, 5, 3)
            t = st.slider("Tendência", 1, 5, 3)
            total_gut = g * u * t
            status = "CRÍTICA" if total_gut >= 100 else "MÉDIA" if total_gut >= 50 else "BAIXA"
            st.write(f"**Prioridade:** {status} ({total_gut})")

        if st.button("💾 Gravar na Planilha"):
            if edificacao_sel and ambiente and patologia:
                nova_linha = pd.DataFrame([{
                    "Campus": campus_sel,
                    "Edificacao": edificacao_sel,
                    "Disciplina": disciplina,
                    "Ambiente": ambiente,
                    "Patologia": patologia,
                    "GUT": total_gut,
                    "Status": status
                }])
                # Adiciona o novo dado ao que já existia
                df_atualizado = pd.concat([df_base, nova_linha], ignore_index=True)
                # Envia de volta para o Google Sheets
                conn.update(data=df_atualizado)
                st.success("Dados salvos com sucesso!")
                st.rerun()
            else:
                st.error("Por favor, preencha todos os campos!")

    # --- EXIBIÇÃO E GRÁFICOS ---
    st.divider()
    if not df_base.empty:
        # Filtra para mostrar apenas o que pertence ao Campus e Edificação selecionados
        df_filtrado = df_base[(df_base['Campus'] == campus_sel) & (df_base['Edificacao'] == edificacao_sel)]
        
        if not df_filtrado.empty:
            st.subheader(f"📋 Itens Registrados: {edificacao_sel}")
            st.dataframe(df_filtrado.drop(columns=["Campus", "Edificacao"]), use_container_width=True)
            
            # Gráfico de Prioridades
            fig = px.bar(df_filtrado, x='Status', title="Resumo de Prioridades", 
                         color='Status', color_discrete_map={"CRÍTICA": "red", "MÉDIA": "orange", "BAIXA": "green"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Nenhum registro encontrado para {campus_sel} - {edificacao_sel}.")
