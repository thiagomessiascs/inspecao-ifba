import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA EQUIPE E MAPA PRODIN ---
EQUIPE = {
    "Eng. Thiago": {"campi": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"]},
    "Eng. Roger": {"campi": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"]},
    "Eng. Laís": {"campi": ["Barreiras", "Jaguaquara", "Jequié"]},
    "Eng. Larissa": {"campi": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacã"]},
    "Eng. Marcelo": {"campi": ["Brumado", "Vitória da Conquista"]},
    "Eng. Fenelon": {"campi": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"]}
}

DADOS_TECNICOS = {
    "Alvenaria": {"patologias": ["Fissura/Trinca", "Umidade ascendente", "Desplacamento", "Outros"], "solucoes": ["Tratamento com tela", "Impermeabilização", "Reboco novo", "Outros"]},
    "Estrutura": {"patologias": ["Corrosão de armadura", "Segregação de concreto", "Fissura estrutural", "Outros"], "solucoes": ["Escarificação e tratamento", "Grouteamento", "Reforço", "Outros"]},
    "Instalação elétrica": {"patologias": ["Fiação exposta", "Disjuntor desarmando", "Lâmpada queimada", "Outros"], "solucoes": ["Revisão de cabeamento", "Troca de componentes", "Substituição LED", "Outros"]},
    "Instalação hidrossanitária": {"patologias": ["Vazamento", "Entupimento", "Mau cheiro", "Outros"], "solucoes": ["Troca de reparo", "Desobstrução", "Revisão de tubulação", "Outros"]},
    "Outros": {"patologias": ["Outros"], "solucoes": ["Outros"]}
}

# --- 2. CONFIGURAÇÃO E LIMPEZA ---
st.set_page_config(page_title="Sistema PRODIN - IFBA", layout="wide")

if "edit_mode" not in st.session_state: st.session_state.edit_mode = None

def limpar_tudo():
    """Limpa todas as chaves de widgets do session_state"""
    for key in ["edif_val", "amb_val", "comp_val", "disc_val", "desc_val", "sol_val"]:
        if key in st.session_state:
            st.session_state[key] = "" if "val" in key else None
    st.session_state.edit_mode = None

# --- 3. LOGIN ---
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
        eng_sel = st.selectbox("Selecione seu nome:", list(EQUIPE.keys())) #
        campi_permitidos = sorted(EQUIPE[eng_sel]["campi"]) #
        campus_sel = st.selectbox("Campus da Vistoria:", campi_permitidos)
        if st.button("Sair"): st.session_state.login = False; st.rerun()

    st.markdown(f'<h1 style="color:#1e4620;">🏢 Sistema de Inspeção Predial - IFBA</h1>', unsafe_allow_html=True)
    
    # --- 4. FORMULÁRIO ---
    with st.container(border=True):
        st.subheader("📝 Detalhes da Patologia")
        c1, c2 = st.columns(2)
        
        with c1:
            edificacao = st.selectbox("Edificação:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca"], key="edif_val")
            ambiente = st.selectbox("Ambiente:", ["Sala de aula", "Laboratório", "Sanitário", "Corredor"], key="amb_val")
            complemento = st.text_input("Nº ou Complemento:", key="comp_val")
            disciplina = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()), key="disc_val")

        with c2:
            if disciplina:
                pat_opcoes = DADOS_TECNICOS[disciplina]["patologias"]
                pat_sel = st.selectbox("Patologia Comum:", pat_opcoes) #
                desc_final = st.text_area("Descrição Técnica:", value=pat_sel if pat_sel != "Outros" else "", key="desc_val")
                
                sol_opcoes = DADOS_TECNICOS[disciplina]["solucoes"]
                sol_sel = st.selectbox("Sugestão de Solução:", sol_opcoes)
                sol_final = st.text_area("Proposta de Intervenção:", value=sol_sel if sol_sel != "Outros" else "", key="sol_val")
            else:
                st.warning("Selecione a disciplina para habilitar os campos.")
                desc_final = sol_final = ""

        # Botão Salvar
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("💾 Salvar Inspeção", use_container_width=True):
                nova_linha = {
                    "Data": datetime.now().strftime("%d/%m/%Y"), "Engenheiro": eng_sel, "Campus": campus_sel,
                    "Edificacao": edificacao, "Ambiente": f"{ambiente} {complemento}", "Disciplina": disciplina,
                    "Descricao": desc_final, "Solucoes": sol_final
                }
                
                if st.session_state.edit_mode is not None:
                    df_base.iloc[st.session_state.edit_mode] = nova_linha
                else:
                    df_base = pd.concat([df_base, pd.DataFrame([nova_linha])], ignore_index=True)
                
                conn.update(data=df_base)
                st.success("✅ Histórico Atualizado!")
                limpar_tudo() # LIMPEZA DOS CAMPOS
                st.rerun()
        with col_btn2:
            if st.session_state.edit_mode is not None:
                if st.button("❌ Cancelar Edição"): limpar_tudo(); st.rerun()

    # --- 5. LISTA DE REGISTROS COM EDITAR/EXCLUIR ---
    st.markdown("---")
    st.subheader(f"📋 Registros em {campus_sel}")
    df_filtro = df_base[df_base['Campus'] == campus_sel].copy()
    
    if not df_filtro.empty:
        st.dataframe(df_filtro[["Edificacao", "Ambiente", "Disciplina", "Descricao"]].tail(10), use_container_width=True)
        
        # Área de Gerenciamento
        st.markdown("**Gerenciar Registro:**")
        sel_idx = st.selectbox("Selecione o item pelo índice (Nº na esquerda):", df_filtro.index)
        
        g1, g2, _ = st.columns([1, 1, 3])
        with g1:
            if st.button("✏️ Editar Item", use_container_width=True):
                item = df_base.loc[sel_idx]
                st.session_state.edit_mode = sel_idx
                # Carrega nos widgets usando as chaves (keys)
                st.session_state.edif_val = item["Edificacao"]
                st.session_state.disc_val = item["Disciplina"]
                st.session_state.desc_val = item["Descricao"]
                st.session_state.sol_val = item["Solucoes"]
                st.rerun()
        
        with g2:
            if st.button("🗑️ Excluir Item", use_container_width=True):
                df_base = df_base.drop(sel_idx)
                conn.update(data=df_base)
                st.toast("Item removido!")
                st.rerun()

    st.markdown(f'<div style="text-align:center; color:#888; font-size:12px; margin-top:50px;">PRODIN - IFBA 2026 | Thiago Messias & Roger Santana</div>', unsafe_allow_html=True)
