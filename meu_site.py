import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA EQUIPE E MAPA DE CAMPI (PRODIN) ---
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
    "Cobertura": {"patologias": ["Telha quebrada", "Infiltração em calha", "Estrutura comprometida", "Outros"], "solucoes": ["Substituição de telhas", "Limpeza e vedação", "Impermeabilização", "Outros"]},
    "Instalação elétrica": {"patologias": ["Fiação exposta", "Disjuntor desarmando", "Lâmpada queimada", "Outros"], "solucoes": ["Revisão de cabeamento", "Troca de componentes", "Substituição LED", "Outros"]},
    "Instalação hidrossanitária": {"patologias": ["Vazamento", "Entupimento", "Mau cheiro", "Outros"], "solucoes": ["Troca de reparo", "Desobstrução", "Revisão de tubulação", "Outros"]},
    "Outros": {"patologias": ["Outros"], "solucoes": ["Outros"]}
}

# --- 2. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide")

# Inicialização de variáveis de controle para limpeza e edição
if "form_data" not in st.session_state:
    st.session_state.form_data = {"edif": None, "amb": None, "comp": "", "disc": None, "pat": None, "sol_sug": None, "desc_txt": "", "sol_txt": "", "idx": None}

def reset_form():
    st.session_state.form_data = {"edif": None, "amb": None, "comp": "", "disc": None, "pat": None, "sol_sug": None, "desc_txt": "", "sol_txt": "", "idx": None}

# --- 3. LOGIN ---
if "login" not in st.session_state: st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login PRODIN")
    senha = st.text_input("Senha de Acesso:", type="password")
    if st.button("Acessar Sistema"):
        if senha == "IFBA2026":
            st.session_state.login = True
            st.rerun()
else:
    # Conexão com Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(ttl="0")

    with st.sidebar:
        st.subheader("🕵️ Vistoriador")
        eng_sel = st.selectbox("Selecione seu nome:", list(EQUIPE.keys())) #
        st.image(EQUIPE[eng_sel]["foto"], width=100)
        
        # Filtro de Campi por Engenheiro
        campi_permitidos = sorted(EQUIPE[eng_sel]["campi"])
        campus_sel = st.selectbox("Campus da Vistoria:", campi_permitidos)
        
        if st.button("Sair"):
            st.session_state.login = False
            st.rerun()

    # --- 4. FORMULÁRIO DE INSPEÇÃO ---
    st.markdown(f'<h1 style="color:#1e4620;">🏢 Sistema de Inspeção Predial - IFBA</h1>', unsafe_allow_html=True)
    
    with st.expander(f"📝 Formulário de Registro - {campus_sel}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            edificacao = st.selectbox("Edificação/Bloco:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca", "Ginásio", "Muro"], 
                                     index=None if st.session_state.form_data["edif"] is None else ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca", "Ginásio", "Muro"].index(st.session_state.form_data["edif"]))
            
            ambiente = st.selectbox("Ambiente:", ["Sala de aula", "Laboratório", "Sanitário", "Corredor", "Pátio"], 
                                    index=None if st.session_state.form_data["amb"] is None else ["Sala de aula", "Laboratório", "Sanitário", "Corredor", "Pátio"].index(st.session_state.form_data["amb"]))
            
            complemento = st.text_input("Nº ou Complemento:", value=st.session_state.form_data["comp"]) if ambiente and ("Sala" in ambiente or "Laboratório" in ambiente) else ""
            
            # DISCIPLINA DISPARA A LÓGICA DE PATOLOGIA
            disciplina = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()), 
                                      index=None if st.session_state.form_data["disc"] is None else list(DADOS_TECNICOS.keys()).index(st.session_state.form_data["disc"]))

        with col2:
            if disciplina:
                # Recupera listas específicas da disciplina
                pats = DADOS_TECNICOS[disciplina]["patologias"]
                sols = DADOS_TECNICOS[disciplina]["solucoes"]
                
                pat_escolhida = st.selectbox("Patologia Comum:", pats, 
                                             index=None if st.session_state.form_data["pat"] is None else pats.index(st.session_state.form_data["pat"]))
                
                desc_final = st.text_area("Descrição Técnica Detalhada:", value=st.session_state.form_data["desc_txt"] if st.session_state.form_data["desc_txt"] else (pat_escolhida if pat_escolhida and pat_escolhida != "Outros" else ""))
                
                sol_escolhida = st.selectbox("Sugestão de Solução:", sols, 
                                             index=None if st.session_state.form_data["sol_sug"] is None else sols.index(st.session_state.form_data["sol_sug"]))
                
                sol_final = st.text_area("Proposta de Intervenção:", value=st.session_state.form_data["sol_txt"] if st.session_state.form_data["sol_txt"] else (sol_escolhida if sol_escolhida and sol_escolhida != "Outros" else ""))
            else:
                st.info("💡 Escolha a Disciplina para ver as patologias e soluções.")
                desc_final = sol_final = ""

        # GUT e Foto
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            foto = st.file_uploader("📸 Registro Fotográfico", type=["jpg", "png", "jpeg"])
        with c2:
            g = st.select_slider("Gravidade", [1,2,3,4,5], 3)
            u = st.select_slider("Urgência", [1,2,3,4,5], 3)
            t = st.select_slider("Tendência", [1,2,3,4,5], 3)
            score = g*u*t

        # BOTÃO SALVAR (Com Limpeza de Campos)
        if st.button("💾 Salvar Inspeção"):
            if edificacao and disciplina:
                nova_entrada = {
                    "Data": datetime.now().strftime("%d/%m/%Y"), "Engenheiro": eng_sel, "Campus": campus_sel,
                    "Edificacao": edificacao, "Ambiente": f"{ambiente} {complemento}", "Disciplina": disciplina,
                    "Descricao": desc_final, "Solucoes": sol_final, "Score_GUT": score
                }
                
                if st.session_state.form_data["idx"] is not None:
                    df_base.iloc[st.session_state.form_data["idx"]] = nova_entrada
                else:
                    df_base = pd.concat([df_base, pd.DataFrame([nova_entrada])], ignore_index=True)
                
                conn.update(data=df_base)
                st.success("✅ Registro processado com sucesso!")
                reset_form()
                st.rerun()
            else:
                st.error("Campos obrigatórios: Edificação e Disciplina.")

    # --- 5. HISTÓRICO E EDIÇÃO ---
    st.markdown("---")
    st.subheader(f"📋 Registros Recentes em {campus_sel}")
    df_campus = df_base[df_base['Campus'] == campus_sel].reset_index()
    
    if not df_campus.empty:
        st.dataframe(df_campus[["Edificacao", "Ambiente", "Disciplina", "Score_GUT"]].tail(10), use_container_width=True)
        
        # Lógica de Edição: Selecionar linha para carregar no formulário
        edit_idx = st.selectbox("Para EDITAR, selecione o registro abaixo:", df_campus.index, format_func=lambda x: f"Item {x} - {df_campus.loc[x, 'Edificacao']} ({df_campus.loc[x, 'Disciplina']})")
        
        if st.button("✏️ Carregar para Edição"):
            item = df_campus.loc[edit_idx]
            # Extrai apenas o nome do ambiente sem o complemento
            amb_puro = item["Ambiente"].split(" ")[0] if " " in item["Ambiente"] else item["Ambiente"]
            comp_puro = item["Ambiente"].replace(amb_puro, "").strip()
            
            st.session_state.form_data = {
                "edif": item["Edificacao"], "amb": amb_puro, "comp": comp_puro, 
                "disc": item["Disciplina"], "pat": None, "sol_sug": None,
                "desc_txt": item["Descricao"], "sol_txt": item["Solucoes"], "idx": item["index"]
            }
            st.rerun()

    # Rodapé
    st.markdown(f'<div style="text-align:center; color:#888; padding-top:30px;">Desenvolvido por: Thiago Messias Carvalho Soares | Roger Ramos Santana<br>Equipe PRODIN - IFBA 2026</div>', unsafe_allow_html=True)
