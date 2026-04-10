import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA EQUIPE PRODIN ---
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
    "Instalação hidrossanitária": {"patologias": ["Vazamento torneira", "Entupimento", "Mau cheiro", "Outros"], "solucoes": ["Troca reparo", "Desobstrução", "Revisão tubulação", "Outros"]},
    "Outros": {"patologias": ["Outros"], "solucoes": ["Outros"]}
}

# --- 2. CONFIGURAÇÃO DA PÁGINA E ESTADO ---
st.set_page_config(page_title="Inspeção Predial - IFBA PRODIN", layout="wide")

# Inicialização de variáveis de controle
if "form_data" not in st.session_state:
    st.session_state.form_data = {"edif": None, "amb": None, "comp": "", "disc": None, "desc_txt": "", "sol_txt": "", "idx": None}

if "login" not in st.session_state: st.session_state.login = False

def limpar_campos():
    st.session_state.form_data = {"edif": None, "amb": None, "comp": "", "disc": None, "desc_txt": "", "sol_txt": "", "idx": None}

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
        eng_sel = st.selectbox("Selecione seu nome:", list(EQUIPE.keys())) #
        st.image(EQUIPE[eng_sel]["foto"], width=100) # FOTO OFICIAL
        
        # Filtro de Campi por Engenheiro
        campi_permitidos = sorted(EQUIPE[eng_sel]["campi"])
        campus_sel = st.selectbox("Campus da Vistoria:", campi_permitidos)
        if st.button("Sair"): st.session_state.login = False; st.rerun()

    # --- 4. TÍTULO E FORMULÁRIO ---
    st.markdown(f'<h1 style="color:#1e4620;">🏢 Sistema de Inspeção Predial - IFBA</h1>', unsafe_allow_html=True)
    
    with st.expander(f"📝 Formulário de Registro - {campus_sel}", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            edif_opc = ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Biblioteca", "Muro"]
            edificacao = st.selectbox("Edificação/Bloco:", edif_opc, index=None if st.session_state.form_data["edif"] is None else edif_opc.index(st.session_state.form_data["edif"]))
            
            amb_opc = ["Sala de aula", "Laboratório", "Sanitário", "Corredor", "Pátio"]
            ambiente = st.selectbox("Ambiente:", amb_opc, index=None if st.session_state.form_data["amb"] is None else amb_opc.index(st.session_state.form_data["amb"]))
            
            complemento = st.text_input("Nº ou Complemento:", value=st.session_state.form_data["comp"]) if ambiente and ("Sala" in ambiente or "Laboratório" in ambiente) else ""
            disciplina = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()), index=None if st.session_state.form_data["disc"] is None else list(DADOS_TECNICOS.keys()).index(st.session_state.form_data["disc"]))

        with col2:
            if disciplina:
                desc_final = st.text_area("Descrição Técnica Detalhada:", value=st.session_state.form_data["desc_txt"])
                sol_final = st.text_area("Proposta de Intervenção:", value=st.session_state.form_data["sol_txt"])
            else:
                st.info("💡 Escolha a Disciplina para habilitar os campos.")
                desc_final = sol_final = ""

        # GUT e Foto
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            foto = st.file_uploader("📸 Registro Fotográfico", type=["jpg", "png", "jpeg"])
        with c2:
            st.write("**Avaliação de Prioridade (GUT)**")
            g = st.select_slider("Gravidade", [1,2,3,4,5], 3)
            u = st.select_slider("Urgência", [1,2,3,4,5], 3)
            t = st.select_slider("Tendência", [1,2,3,4,5], 3)
            score = g*u*t
            st.info(f"Score GUT: {score}")

        # BOTÃO SALVAR (Com Limpeza de Campos CORRIGIDA)
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("💾 Salvar Inspeção", use_container_width=True):
                if edificacao and disciplina:
                    nova_linha = {
                        "Data": datetime.now().strftime("%d/%m/%Y"), "Engenheiro": eng_sel, "Campus": campus_sel,
                        "Edificacao": edificacao, "Ambiente": f"{ambiente} {complemento}", "Disciplina": disciplina,
                        "Descricao": desc_final, "Solucoes": sol_final, "Score_GUT": score
                    }
                    if st.session_state.form_data["idx"] is not None:
                        # Lógica de EDIÇÃO: sobrescreve a linha
                        df_base.iloc[st.session_state.form_data["idx"]] = nova_linha
                    else:
                        # Lógica de NOVO REGISTRO
                        df_base = pd.concat([df_base, pd.DataFrame([nova_linha])], ignore_index=True)
                    
                    conn.update(data=df_base)
                    st.success("✅ Histórico processado!")
                    limpar_campos() # LIMPEZA EFETIVA DO CÉREBRO DO FORM
                    st.rerun()
                else:
                    st.error("Preencha Edificação e Disciplina.")
        with col_btn2:
            if st.session_state.form_data["idx"] is not None:
                if st.button("❌ Cancelar Edição"): limpar_campos(); st.rerun()

    # --- 5. TABELA DE HISTÓRICO COM EDIÇÃO CORRIGIDA ---
    st.markdown("---")
    st.subheader(f"📋 Registros Recentes em {campus_sel}")
    df_campus = df_base[df_base['Campus'] == campus_sel].reset_index()
    
    if not df_campus.empty:
        st.dataframe(df_campus[["Data", "Edificacao", "Ambiente", "Disciplina", "Score_GUT"]].tail(10), use_container_width=True)
        
        # Área de Edição Inteligente
        sel_idx = st.selectbox("Para EDITAR, selecione o registro abaixo pelo número (esquerda):", df_campus.index)
        
        if st.button("✏️ Carregar para Edição"):
            item_real = df_campus.loc[sel_idx]
            amb_puro = item_real["Ambiente"].split(" ")[0] if " " in item_real["Ambiente"] else item_real["Ambiente"]
            comp_puro = item_real["Ambiente"].replace(amb_puro, "").strip()
            
            # Carrega nos Widgets usando o st.session_state
            st.session_state.form_data = {
                "edif": item_real["Edificacao"], "amb": amb_puro, "comp": comp_puro, 
                "disc": item_real["Disciplina"], "desc_txt": item_real["Descricao"], 
                "sol_txt": item_real["Solucoes"], "idx": item_real["index"] # Guardamos o índice real da planilha
            }
            st.rerun()

    # Rodapé Institucional
    st.markdown(f'<div style="text-align:center; color:#888; font-size:12px; margin-top:50px;">Equipe PRODIN - IFBA 2026 | Thiago Messias Carvalho Soares | Roger Ramos Santana</div>', unsafe_allow_html=True)
