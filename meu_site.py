import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA EQUIPE E MAPA PRODIN ---
EQUIPE = {
    "Eng. Thiago": {"campi": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"], "foto": "https://github.com/thiagomessiascs/inspecao-ifba/blob/main/Thiago.jpg?raw=true"},
    "Eng. Roger": {"campi": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"], "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"},
    "Eng. Laís": {"campi": ["Barreiras", "Jaguaquara", "Jequié"], "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135768.png"},
    "Eng. Larissa": {"campi": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacã"], "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135768.png"},
    "Eng. Marcelo": {"campi": ["Brumado", "Vitória da Conquista"], "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"},
    "Eng. Fenelon": {"campi": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"], "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"}
}

DADOS_TECNICOS = {
    "Alvenaria": {"patologias": ["Fissura/Trinca", "Umidade ascendente", "Desplacamento", "Outros"], "solucoes": ["Tratamento com tela", "Impermeabilização", "Reboco novo", "Outros"]},
    "Estrutura": {"patologias": ["Corrosão de armadura", "Segregação de concreto", "Fissura estrutural", "Outros"], "solucoes": ["Escarificação e tratamento", "Grouteamento", "Reforço", "Outros"]},
    "Instalação elétrica": {"patologias": ["Fiação exposta", "Disjuntor desarmando", "Lâmpada queimada", "Outros"], "solucoes": ["Revisão fiação", "Troca componentes", "Substituição LED", "Outros"]},
    "Instalação hidrossanitária": {"patologias": ["Vazamento", "Entupimento", "Mau cheiro", "Outros"], "solucoes": ["Troca reparo", "Desobstrução", "Revisão tubulação", "Outros"]},
    "Outros": {"patologias": ["Outros"], "solucoes": ["Outros"]}
}

st.set_page_config(page_title="Sistema PRODIN - IFBA", layout="wide")

# --- 2. FUNÇÕES DE SUPORTE ---
@st.dialog("✏️ Editar Registro")
def editar_registro(index, row_data, conn, df_full):
    st.write(f"Editando item da unidade: **{row_data['Edificacao']}**")
    new_edif = st.selectbox("Edificação:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca", "Muro"], index=["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca", "Muro"].index(row_data['Edificacao']))
    new_disc = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()), index=list(DADOS_TECNICOS.keys()).index(row_data['Disciplina']))
    new_desc = st.text_area("Descrição:", value=row_data['Descricao'])
    new_sol = st.text_area("Solução:", value=row_data['Solucoes'])
    
    if st.button("Confirmar Alterações"):
        df_full.loc[index, "Edificacao"] = new_edif
        df_full.loc[index, "Disciplina"] = new_disc
        df_full.loc[index, "Descricao"] = new_desc
        df_full.loc[index, "Solucoes"] = new_sol
        conn.update(data=df_full)
        st.success("Alterado com sucesso!")
        st.rerun()

# --- 3. LOGIN E INTERFACE ---
if "login" not in st.session_state: st.session_state.login = False
if not st.session_state.login:
    st.title("🔐 Login PRODIN")
    if st.text_input("Senha:", type="password") == "IFBA2026":
        if st.button("Acessar"): st.session_state.login = True; st.rerun()
else:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(ttl="0")

    with st.sidebar:
        st.subheader("🕵️ Vistoriador")
        eng_sel = st.selectbox("Nome:", list(EQUIPE.keys()))
        st.image(EQUIPE[eng_sel]["foto"], width=100)
        campi_perm = sorted(EQUIPE[eng_sel]["campi"])
        campus_sel = st.selectbox("Campus:", campi_perm)
        if st.button("Sair"): st.session_state.login = False; st.rerun()

    st.markdown(f'<h1 style="color:#1e4620;">🏢 Inspeção Predial - IFBA</h1>', unsafe_allow_html=True)
    
    # --- 4. FORMULÁRIO DE CADASTRO (LIMPO) ---
    with st.expander("➕ Novo Registro de Inspeção", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            edif = st.selectbox("Edificação:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca", "Muro"], key="reg_edif")
            amb = st.selectbox("Ambiente:", ["Sala de aula", "Laboratório", "Sanitário", "Corredor"], key="reg_amb")
            disc = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()), key="reg_disc") #
        with c2:
            if disc: # Aparece patologia e solução conforme disciplina
                pat_sug = st.selectbox("Patologias Comuns:", DADOS_TECNICOS[disc]["patologias"])
                desc = st.text_area("Descrição Detalhada:", value=pat_sug if pat_sug != "Outros" else "")
                sol_sug = st.selectbox("Soluções Comuns:", DADOS_TECNICOS[disc]["solucoes"])
                sol = st.text_area("Proposta de Intervenção:", value=sol_sug if sol_sug != "Outros" else "")
        
        if st.button("💾 Salvar Inspeção"):
            novo_df = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y"), "Engenheiro": eng_sel, "Campus": campus_sel, "Edificacao": edif, "Ambiente": amb, "Disciplina": disc, "Descricao": desc, "Solucoes": sol}])
            df_final = pd.concat([df_base, novo_df], ignore_index=True)
            conn.update(data=df_final)
            st.success("Salvo!")
            st.rerun()

    # --- 5. HISTÓRICO COM GERENCIAMENTO (SEM ERROS) ---
    st.markdown("---")
    st.subheader(f"📋 Registros em {campus_sel}")
    df_view = df_base[df_base['Campus'] == campus_sel].copy()
    
    if not df_view.empty:
        st.dataframe(df_view[["Edificacao", "Ambiente", "Disciplina", "Descricao"]].tail(10), use_container_width=True)
        
        st.write("**Ações sobre o Registro:**")
        idx_to_manage = st.selectbox("Selecione o item (pelo ID à esquerda):", df_view.index)
        
        col_edit, col_del, _ = st.columns([1, 1, 3])
        with col_edit:
            if st.button("✏️ Editar Item"):
                editar_registro(idx_to_manage, df_base.loc[idx_to_manage], conn, df_base) # CHAMA O MODAL ISOLADO
        with col_del:
            if st.button("🗑️ Excluir"):
                df_base = df_base.drop(idx_to_manage)
                conn.update(data=df_base)
                st.rerun()

    st.markdown(f'<div style="text-align:center; color:#888; font-size:12px; margin-top:30px;">PRODIN 2026</div>', unsafe_allow_html=True)
