import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io
import requests
import base64

# --- 1. BANCO DE DADOS HIERÁRQUICO (DISCIPLINA -> PATOLOGIA -> SOLUÇÃO) ---
DADOS_TECNICOS = {
    "Alvenaria": {
        "patologias": ["Fissura/Trinca", "Umidade ascendente", "Desplacamento", "Eflorescência", "Infiltração por fachada"],
        "solucoes": ["Tratamento com tela", "Impermeabilização de baldrame", "Reboco novo", "Limpeza química", "Pintura impermeabilizante"]
    },
    "Estrutura": {
        "patologias": ["Corrosão de armadura", "Segregação de concreto", "Flecha excessiva", "Fissura estrutural"],
        "solucoes": ["Escarificação e tratamento de aço", "Grouteamento", "Reforço estrutural", "Escoramento técnico"]
    },
    "Cobertura": {
        "patologias": ["Telha quebrada", "Infiltração em calha", "Estrutura comprometida", "Goteira/Umidade no forro"],
        "solucoes": ["Substituição de telhas", "Limpeza e vedação de calhas", "Substituição de peças", "Impermeabilização de laje"]
    },
    "Pavimentação": {
        "patologias": ["Piso solto", "Desgaste excessivo", "Buraco/Depressão", "Rachadura/Recalque"],
        "solucoes": ["Substituição de revestimento", "Regularização de base", "Rejuntamento", "Aplicação de resina/selador"]
    },
    "Revestimento": {
        "patologias": ["Desplacamento cerâmico", "Pintura descascando", "Fungo/Bolor", "Fisura no emboço"],
        "solucoes": ["Substituição de placas", "Lixamento e nova pintura", "Limpeza com hipoclorito", "Tratamento de base"]
    },
    "Esquadrias": {
        "patologias": ["Vidro quebrado", "Ferrugem", "Dificuldade de fechamento", "Falta de vedação"],
        "solucoes": ["Troca de vidro", "Pintura anticorrosiva", "Ajuste/Lubrificação", "Troca de guarnições"]
    },
    "Instalação elétrica": {
        "patologias": ["Fiação exposta", "Disjuntor desarmando", "Quadro sem identificação", "Lâmpada/Reator queimado"],
        "solucoes": ["Revisão de cabeamento", "Troca de disjuntores", "Identificação de circuitos", "Substituição por LED"]
    },
    "Instalação hidrossanitária": {
        "patologias": ["Vazamento em torneira/válvula", "Entupimento", "Mau cheiro", "Infiltração de esgoto/água"],
        "solucoes": ["Troca de reparo/vedante", "Desobstrução", "Sifonagem adequada", "Revisão de tubulação"]
    },
    "Outros": {"patologias": ["Especificar no campo livre"], "solucoes": ["Especificar no campo livre"]}
}

# --- 2. EQUIPE COMPLETA PRODIN ---
EQUIPE = {
    "Eng. Thiago": {"nome": "Thiago Messias Carvalho Soares", "foto": "https://github.com/thiagomessiascs/inspecao-ifba/blob/main/Thiago.jpg?raw=true"},
    "Eng. Roger": {"nome": "Roger Ramos Santana", "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"},
    "Eng. Fenelon": {"nome": "Fenelon Rocha", "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"},
    "Eng. Laís": {"nome": "Laís Oliveira", "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135768.png"},
    "Eng. Larissa": {"nome": "Larissa Santos", "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135768.png"},
    "Eng. Marcelo": {"nome": "Marcelo Almeida", "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"}
}

CAMPI = ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo", "Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"]

# --- 3. INTERFACE ---
st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide")

# CSS para Banner e Estilo
st.markdown("""
    <style>
    .main-header { border: 2px solid #2e7d32; border-left: 15px solid #2e7d32; padding: 25px; border-radius: 10px; background-color: #ffffff; display: flex; align-items: center; margin-bottom: 20px; }
    .profile-pic { width: 100px; height: 100px; border-radius: 50%; border: 3px solid #2e7d32; object-fit: cover; }
    </style>
""", unsafe_allow_html=True)

if "login" not in st.session_state: st.session_state["login"] = False

if not st.session_state["login"]:
    st.title("🔐 Login PRODIN")
    if st.text_input("Senha:", type="password") == "IFBA2026":
        if st.button("Acessar"): st.session_state["login"] = True; st.rerun()
else:
    # Conexão GSheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(ttl="0")

    with st.sidebar:
        st.subheader("🕵️ Vistoriador")
        eng_sel = st.selectbox("Selecione seu nome:", list(EQUIPE.keys())) # Recuperado
        st.markdown(f'<img src="{EQUIPE[eng_sel]["foto"]}" class="profile-pic">', unsafe_allow_html=True)
        campus_sel = st.selectbox("Campus da Vistoria:", sorted(CAMPI))
        if st.button("Sair"): st.session_state["login"] = False; st.rerun()

    # Banner Principal com Ícone
    st.markdown(f'''
        <div class="main-header">
            <img src="https://cdn-icons-png.flaticon.com/512/4320/4320350.png" width="80" style="margin-right:20px;">
            <div>
                <h1 style="color:#1e4620; margin:0;">Sistema de Inspeção Predial - IFBA</h1>
                <p style="color:#666; margin:0;">Engenharia, Manutenção e Vistorias Técnicas</p>
            </div>
        </div>
    ''', unsafe_allow_html=True)

    # CORREÇÃO DA HIERARQUIA: Usamos colunas fora do form para o gatilho funcionar
    st.markdown(f"### 📝 Registro: {campus_sel}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        edif = st.selectbox("Edificação/Bloco:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Ginásio", "Guarita", "Estacionamento", "Passeio", "Muro", "Biblioteca"], index=None, placeholder="Selecione o Bloco")
        amb_base = st.selectbox("Ambiente:", ["Sala de aula", "Laboratório", "Sanitário PCD", "Sanitário Comum", "Sala administrativa", "Corredor", "Pátio"], index=None, placeholder="Selecione o ambiente")
        
        comp = ""
        if amb_base and ("Sala" in amb_base or "Laboratório" in amb_base):
            comp = st.text_input("Nº ou Complemento:", placeholder="Ex: Sala 43")
            
        disc = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()), index=None, placeholder="Selecione a disciplina...")

    with col2:
        # Lógica Reativa: Se a disciplina for selecionada, o aviso some e as listas aparecem
        if disc:
            pat_list = DADOS_TECNICOS[disc]["patologias"]
            pat_escolhida = st.selectbox("Patologia Comum:", pat_list, index=None, placeholder="O que foi identificado?")
            desc_final = st.text_area("Descrição Técnica Detalhada:", value=pat_escolhida if pat_escolhida else "")
            
            sol_list = DADOS_TECNICOS[disc]["solucoes"]
            sol_escolhida = st.selectbox("Sugestão de Solução:", sol_list, index=None, placeholder="Como resolver?")
            sol_final = st.text_area("Proposta de Intervenção:", value=sol_escolhida if sol_escolhida else "")
        else:
            st.info("💡 Escolha a Disciplina para carregar as patologias e soluções.")
            desc_final = sol_final = ""

    # Botão de Salvar (Dentro de um form simplificado para envio)
    with st.form("envio_dados"):
        st.write("**Avaliação de Prioridade (GUT)**")
        g, u, t = st.columns(3)
        with g: grav = st.select_slider("Gravidade", [1,2,3,4,5], 3)
        with u: urg = st.select_slider("Urgência", [1,2,3,4,5], 3)
        with t: tend = st.select_slider("Tendência", [1,2,3,4,5], 3)
        
        score = grav * urg * tend
        prioridade = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
        st.info(f"Prioridade Atual: {prioridade} (Score: {score})")

        if st.form_submit_button("💾 Salvar Inspeção e Gerar Registro"):
            if edif and disc:
                st.success(f"Item registrado com sucesso para {edif}!")
                # Aqui entra a lógica de concatenação do df e conn.update() como nos anteriores
            else:
                st.error("Por favor, preencha Edificação e Disciplina.")

    # Rodapé Profissional
    st.markdown("---")
    st.caption(f"Logado como: {EQUIPE[eng_sel]['nome']} | PRODIN - IFBA 2026")
