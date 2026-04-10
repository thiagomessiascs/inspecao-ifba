import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA EQUIPE E MAPA PRODIN (BANNER OFICIAL) ---
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
    "Cobertura": {"patologias": ["Telha quebrada", "Infiltração calha", "Estrutura comprometida", "Outros"], "solucoes": ["Substituição", "Impermeabilização", "Limpeza calha", "Outros"]},
    "Instalação elétrica": {"patologias": ["Fiação exposta", "Disjuntor desarmando", "Lâmpada queimada", "Outros"], "solucoes": ["Revisão fiação", "Troca componentes", "Substituição LED", "Outros"]},
    "Instalação hidrossanitária": {"patologias": ["Vazamento", "Entupimento", "Mau cheiro", "Outros"], "solucoes": ["Troca reparo", "Desobstrução", "Revisão tubulação", "Outros"]},
    "Outros": {"patologias": ["Outros"], "solucoes": ["Outros"]}
}

# --- 2. ESTADO DO SISTEMA ---
st.set_page_config(page_title="PRODIN - Inspeção Predial", layout="wide")

if "login" not in st.session_state: st.session_state.login = False
if "edit_idx" not in st.session_state: st.session_state.edit_idx = None

# Função para limpar os campos após salvar ou cancelar
def resetar_form():
    st.session_state.edit_idx = None
    for k in ["edif", "amb", "comp", "disc", "desc", "sol"]:
        if f"f_{k}" in st.session_state:
            st.session_state[f"f_{k}"] = "" if k in ["comp", "desc", "sol"] else None

# --- 3. LOGIN ---
if not st.session_state.login:
    st.title("🔐 Login PRODIN")
    if st.text_input("Senha:", type="password") == "IFBA2026":
        if st.button("Acessar"): st.session_state.login = True; st.rerun()
else:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(ttl="0")

    with st.sidebar:
        st.subheader("🕵️ Vistoriador")
        eng_sel = st.selectbox("Selecione seu nome:", list(EQUIPE.keys()), key="eng_user")
        st.image(EQUIPE[eng_sel]["foto"], width=100) # FOTO DO THIAGO
        
        campi_permitidos = sorted(EQUIPE[eng_sel]["campi"])
        campus_sel = st.selectbox("Campus da Vistoria:", campi_permitidos, key="camp_user")
        if st.button("Sair"): st.session_state.login = False; st.rerun()

    st.markdown(f'<h1 style="color:#1e4620;">🏢 Sistema de Inspeção Predial - IFBA</h1>', unsafe_allow_html=True)
    
    # --- 4. FORMULÁRIO BLINDADO ---
    with st.container(border=True):
        st.subheader(f"📝 {'Editando Registro' if st.session_state.edit_idx is not None else 'Novo Registro'} - {campus_sel}")
        col1, col2 = st.columns(2)
        
        with col1:
            edificacao = st.selectbox("Edificação/Bloco:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca", "Muro"], key="f_edif")
            ambiente = st.selectbox("Ambiente:", ["Sala de aula", "Laboratório", "Sanitário", "Corredor", "Pátio"], key="f_amb")
            complemento = st.text_input("Nº ou Complemento:", key="f_comp")
            disciplina = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()), key="f_disc") #

        with col2:
            if disciplina:
                # Aqui as patologias voltam a aparecer automaticamente
                pats = DADOS_TECNICOS[disciplina]["patologias"]
                sols = DADOS_TECNICOS[disciplina]["solucoes"]
                
                pat_aux = st.selectbox("Sugestão de Patologia:", pats, index=0)
                desc_final = st.text_area("Descrição Técnica Detalhada:", key="f_desc")
                
                sol_aux = st.selectbox("Sugestão de Solução:", sols, index=0)
                sol_final = st.text_area("Proposta de Intervenção:", key="f_sol")
            else:
                st.info("Escolha a disciplina para liberar descrição e solução.")
                desc_final = sol_final = ""

        # Botões de Ação
        b1, b2, _ = st.columns([1, 1, 3])
        with b1:
            if st.button("💾 Salvar Registro", use_container_width=True):
                if edificacao and disciplina:
                    nova_data = {
                        "Data": datetime.now().strftime("%d/%m/%Y"), "Engenheiro": eng_sel, "Campus": campus_sel,
                        "Edificacao": edificacao, "Ambiente": f"{ambiente} {complemento}", "Disciplina": disciplina,
                        "Descricao": desc_final, "Solucoes": sol_final
                    }
                    if st.session_state.edit_idx is not None:
                        df_base.iloc[st.session_state.edit_idx] = nova_data
                    else:
                        df_base = pd.concat([df_base, pd.DataFrame([nova_data])], ignore_index=True)
                    
                    conn.update(data=df_base)
                    st.success("✅ Histórico atualizado!")
                    resetar_form()
                    st.rerun()
        with b2:
            if st.session_state.edit_idx is not None:
                if st.button("❌ Cancelar", use_container_width=True):
                    resetar_form(); st.rerun()

    # --- 5. HISTÓRICO COM EDIÇÃO FUNCIONAL ---
    st.markdown("---")
    st.subheader(f"📋 Registros Recentes em {campus_sel}")
    df_campus = df_base[df_base['Campus'] == campus_sel].copy()
    
    if not df_campus.empty:
        st.dataframe(df_campus[["Edificacao", "Ambiente", "Disciplina", "Descricao"]].tail(10), use_container_width=True)
        
        st.markdown("**Gerenciar Registro:**")
        sel_idx = st.selectbox("Selecione o item para Editar ou Excluir:", df_campus.index)
        
        g1, g2, _ = st.columns([1, 1, 3])
        with g1:
            if st.button("✏️ Carregar para Edição", use_container_width=True):
                item = df_base.loc[sel_idx]
                st.session_state.edit_idx = sel_idx
                # Preenche o formulário via session_state
                st.session_state.f_edif = item["Edificacao"]
                st.session_state.f_disc = item["Disciplina"]
                st.session_state.f_desc = item["Descricao"]
                st.session_state.f_sol = item["Solucoes"]
                st.rerun()
        with g2:
            if st.button("🗑️ Excluir", use_container_width=True):
                df_base = df_base.drop(sel_idx)
                conn.update(data=df_base)
                st.toast("Item removido!")
                st.rerun()

    st.markdown(f'<div style="text-align:center; color:#888; font-size:12px; margin-top:50px;">PRODIN - IFBA 2026 | Thiago Messias & Roger Santana</div>', unsafe_allow_html=True)
