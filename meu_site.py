import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA EQUIPE E CAMPI (MAPA PRODIN) ---
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
    "Instalação elétrica": {"patologias": ["Fiação exposta", "Disjuntor desarmando", "Lâmpada queimada", "Outros"], "solucoes": ["Revisão de cabeamento", "Troca de componentes", "Substituição LED", "Outros"]},
    "Instalação hidrossanitária": {"patologias": ["Vazamento", "Entupimento", "Mau cheiro", "Outros"], "solucoes": ["Troca de reparo", "Desobstrução", "Revisão de tubulação", "Outros"]},
    "Outros": {"patologias": ["Outros"], "solucoes": ["Outros"]}
}

# --- 2. INTERFACE E ESTADO ---
st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide")

# Inicialização do Estado (Para Edição e Limpeza)
if "form_data" not in st.session_state:
    st.session_state.form_data = {"edif": None, "amb": None, "comp": "", "disc": None, "desc": "", "sol": "", "idx": None}

def limpar_campos():
    st.session_state.form_data = {"edif": None, "amb": None, "comp": "", "disc": None, "desc": "", "sol": "", "idx": None}

# Login (Simplificado)
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
        eng_sel = st.selectbox("Selecione seu nome:", list(EQUIPE.keys()))
        st.image(EQUIPE[eng_sel]["foto"], width=80)
        campi_permitidos = sorted(EQUIPE[eng_sel]["campi"])
        campus_sel = st.selectbox("Campus:", campi_permitidos)
        if st.button("Sair"): st.session_state.login = False; st.rerun()

    st.markdown(f'<h1 style="color:#1e4620;">🏢 Sistema de Inspeção - IFBA</h1>', unsafe_allow_html=True)
    
    # FORMULÁRIO DINÂMICO
    with st.expander("📝 Formulário de Inspeção", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            edif = st.selectbox("Edificação:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca"], 
                                index=None if st.session_state.form_data["edif"] is None else ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca"].index(st.session_state.form_data["edif"]))
            amb = st.selectbox("Ambiente:", ["Sala de aula", "Laboratório", "Sanitário", "Corredor"], 
                               index=None if st.session_state.form_data["amb"] is None else ["Sala de aula", "Laboratório", "Sanitário", "Corredor"].index(st.session_state.form_data["amb"]))
            disc = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()), 
                                index=None if st.session_state.form_data["disc"] is None else list(DADOS_TECNICOS.keys()).index(st.session_state.form_data["disc"]))
        
        with col2:
            if disc:
                desc = st.text_area("Descrição da Patologia:", value=st.session_state.form_data["desc"])
                sol = st.text_area("Proposta de Solução:", value=st.session_state.form_data["sol"])
            else:
                st.info("Selecione a disciplina para liberar os textos.")
                desc = sol = ""

        # Botão de Ação (Salvar ou Atualizar)
        if st.button("💾 Salvar Inspeção"):
            nova_linha = {
                "Data": datetime.now().strftime("%d/%m/%Y"), "Engenheiro": eng_sel, "Campus": campus_sel,
                "Edificacao": edif, "Ambiente": amb, "Disciplina": disc, "Descricao": desc, "Solucoes": sol
            }
            
            if st.session_state.form_data["idx"] is not None:
                # Lógica de EDIÇÃO: substitui a linha existente
                df_base.iloc[st.session_state.form_data["idx"]] = nova_linha
            else:
                # Lógica de NOVO REGISTRO
                df_base = pd.concat([df_base, pd.DataFrame([nova_linha])], ignore_index=True)
            
            conn.update(data=df_base)
            st.success("✅ Histórico atualizado!")
            limpar_campos() # Limpa o cérebro do form
            st.rerun()

    # TABELA DE HISTÓRICO COM EDIÇÃO
    st.markdown("---")
    st.subheader(f"📋 Registros em {campus_sel} (Clique para editar)")
    df_filtrado = df_base[df_base['Campus'] == campus_sel].reset_index()
    
    if not df_filtrado.empty:
        # Mostramos a tabela e usamos o st.dataframe para visualização
        st.dataframe(df_filtrado[["Edificacao", "Ambiente", "Disciplina", "Descricao"]].tail(10), use_container_width=True)
        
        # Lógica de Seleção para Editar
        item_para_editar = st.selectbox("Selecione o número da linha para EDITAR:", df_filtrado.index, format_func=lambda x: f"Linha {x} - {df_filtrado.loc[x, 'Edificacao']}")
        
        if st.button("✏️ Carregar para Edição"):
            item_real = df_filtrado.loc[item_para_editar]
            st.session_state.form_data = {
                "edif": item_real["Edificacao"], "amb": item_real["Ambiente"], 
                "disc": item_real["Disciplina"], "desc": item_real["Descricao"], 
                "sol": item_real["Solucoes"], "idx": item_real["index"] # Guardamos o índice real da planilha
            }
            st.rerun()

    st.markdown(f'<div style="text-align:center; color:#888; padding-top:20px;">Desenvolvido por: Thiago Messias Carvalho Soares | Roger Ramos Santana</div>', unsafe_allow_html=True)
