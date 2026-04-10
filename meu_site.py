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

st.set_page_config(page_title="PRODIN - Inspeção Predial", layout="wide")

# --- 2. LÓGICA DE EDIÇÃO VIA DIALOG (POP-UP) ---
@st.dialog("✏️ Editar Registro")
def editar_registro(index, row_data, conn, df_full):
    st.write(f"Editando item: **{row_data['Edificacao']}**")
    new_edif = st.selectbox("Edificação:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca", "Muro"], 
                            index=["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca", "Muro"].index(row_data['Edificacao']))
    new_disc = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()), index=list(DADOS_TECNICOS.keys()).index(row_data['Disciplina']))
    new_desc = st.text_area("Descrição:", value=row_data['Descricao'])
    new_sol = st.text_area("Solução:", value=row_data['Solucoes'])
    
    if st.button("Salvar Alterações"):
        df_full.loc[index, "Edificacao"] = new_edif
        df_full.loc[index, "Disciplina"] = new_disc
        df_full.loc[index, "Descricao"] = new_desc
        df_full.loc[index, "Solucoes"] = new_sol
        conn.update(data=df_full)
        st.success("Registro atualizado com sucesso!")
        st.rerun()

# --- 3. LOGIN E BARRA LATERAL ---
if "login" not in st.session_state: st.session_state.login = False
if not st.session_state.login:
    st.title("🔐 Login PRODIN")
    if st.text_input("Senha:", type="password") == "IFBA2026":
        if st.button("Acessar"): st.session_state.login = True; st.rerun()
else:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(ttl="0")

    with st.sidebar:
        st.markdown("<h3 style='text-align: center;'>🕵️ Vistoriador</h3>", unsafe_allow_html=True)
        eng_sel = st.selectbox("Nome:", list(EQUIPE.keys()))
        
        # Centralização da Foto
        col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
        with col_img2:
            st.image(EQUIPE[eng_sel]["foto"], width=120)
        
        st.markdown("---")
        campi_perm = sorted(EQUIPE[eng_sel]["campi"])
        campus_sel = st.selectbox("Campus da Vistoria:", campi_perm)
        
        if st.button("Sair"): st.session_state.login = False; st.rerun()

    # --- 4. FORMULÁRIO DE REGISTRO ---
    st.markdown(f'<h1 style="color:#1e4620;">🏢 Inspeção Predial - {campus_sel}</h1>', unsafe_allow_html=True)
    
    with st.expander("📝 Formulário de Registro", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            edif = st.selectbox("Edificação/Bloco:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca", "Muro"])
            amb = st.selectbox("Ambiente:", ["Sala de aula", "Laboratório", "Sanitário", "Corredor", "Pátio"])
            disc = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()))
        with c2:
            if disc: # Lógica de patologias dinâmicas
                pat_sug = st.selectbox("Sugestão de Patologia:", DADOS_TECNICOS[disc]["patologias"])
                desc = st.text_area("Descrição Detalhada:", value=pat_sug if pat_sug != "Outros" else "")
                sol_sug = st.selectbox("Sugestão de Solução:", DADOS_TECNICOS[disc]["solucoes"])
                sol = st.text_area("Proposta de Intervenção:", value=sol_sug if sol_sug != "Outros" else "")
        
        if st.button("💾 Salvar Inspeção"):
            novo_item = {
                "Data": datetime.now().strftime("%d/%m/%Y"), "Engenheiro": eng_sel, "Campus": campus_sel,
                "Edificacao": edif, "Ambiente": amb, "Disciplina": disc, "Descricao": desc, "Solucoes": sol
            }
            df_final = pd.concat([df_base, pd.DataFrame([novo_item])], ignore_index=True)
            conn.update(data=df_final)
            st.success("Dados salvos com sucesso!")
            st.rerun()

    # --- 5. HISTÓRICO E GESTÃO ---
    st.markdown("---")
    st.subheader(f"📋 Registros Recentes - {campus_sel}")
    df_campus = df_base[df_base['Campus'] == campus_sel].copy()
    
    if not df_campus.empty:
        st.dataframe(df_campus[["Edificacao", "Ambiente", "Disciplina", "Descricao"]].tail(10), use_container_width=True)
        
        st.write("**Gerenciar Registro:**")
        id_selecionado = st.selectbox("Selecione o item (pelo ID à esquerda):", df_campus.index)
        
        b_edit, b_del, _ = st.columns([1, 1, 3])
        with b_edit:
            if st.button("✏️ Editar Item"):
                editar_registro(id_selecionado, df_base.loc[id_selecionado], conn, df_base) # Edição blindada
        with b_del:
            if st.button("🗑️ Excluir"):
                df_base = df_base.drop(id_selecionado)
                conn.update(data=df_base)
                st.rerun()

    # --- RODAPÉ COM NOMES DOS DESENVOLVEDORES ---
    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align:center; color:#888; font-size:12px;">
            <b>Desenvolvido por:</b> Eng. Thiago Messias Carvalho Soares & Eng. Roger Ramos Santana <br>
            PRODIN - IFBA 2026 | Sistema de Apoio à Engenharia e Manutenção
        </div>
        """, 
        unsafe_allow_html=True
    )
