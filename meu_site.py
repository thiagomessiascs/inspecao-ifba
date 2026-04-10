import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io
import requests
import base64

# --- 1. CONFIGURAÇÃO DA EQUIPE E CAMPI (MAPA PRODIN) ---
# Dados extraídos do mapa oficial
EQUIPE = {
    "Eng. Thiago": {
        "campi": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"],
        "foto": "https://github.com/thiagomessiascs/inspecao-ifba/blob/main/Thiago.jpg?raw=true"
    },
    "Eng. Roger": {
        "campi": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    },
    "Eng. Laís": {
        "campi": ["Barreiras", "Jaguaquara", "Jequié"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135768.png"
    },
    "Eng. Larissa": {
        "campi": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacã"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135768.png"
    },
    "Eng. Marcelo": {
        "campi": ["Brumado", "Vitória da Conquista"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    },
    "Eng. Fenelon": {
        "campi": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    }
}

# --- 2. BANCO DE DADOS TÉCNICO COM OPÇÃO "OUTROS" ---
DADOS_TECNICOS = {
    "Alvenaria": {
        "patologias": ["Fissura/Trinca", "Umidade ascendente", "Desplacamento", "Eflorescência", "Outros"],
        "solucoes": ["Tratamento com tela", "Impermeabilização", "Reboco novo", "Limpeza química", "Outros"]
    },
    "Estrutura": {
        "patologias": ["Corrosão de armadura", "Segregação de concreto", "Fissura estrutural", "Outros"],
        "solucoes": ["Escarificação e tratamento", "Grouteamento", "Reforço", "Outros"]
    },
    "Instalação elétrica": {
        "patologias": ["Fiação exposta", "Disjuntor desarmando", "Lâmpada queimada", "Outros"],
        "solucoes": ["Revisão de cabeamento", "Troca de componentes", "Substituição LED", "Outros"]
    },
    "Instalação hidrossanitária": {
        "patologias": ["Vazamento", "Entupimento", "Mau cheiro", "Outros"],
        "solucoes": ["Troca de reparo", "Desobstrução", "Revisão de tubulação", "Outros"]
    },
    "Outros": {"patologias": ["Outros"], "solucoes": ["Outros"]}
}

# --- 3. INTERFACE E LÓGICA ---
st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide")

# Estilo do Banner
st.markdown("""
    <style>
    .main-header { border: 2px solid #2e7d32; border-left: 15px solid #2e7d32; padding: 25px; border-radius: 10px; background-color: #ffffff; display: flex; align-items: center; margin-bottom: 20px; }
    .profile-pic { width: 100px; height: 100px; border-radius: 50%; border: 3px solid #2e7d32; object-fit: cover; margin: 10px auto; display: block; }
    </style>
""", unsafe_allow_html=True)

if "login" not in st.session_state: st.session_state["login"] = False

if not st.session_state["login"]:
    st.title("🔐 Login PRODIN")
    if st.text_input("Senha:", type="password") == "IFBA2026":
        if st.button("Acessar"): st.session_state["login"] = True; st.rerun()
else:
    with st.sidebar:
        st.subheader("🕵️ Vistoriador")
        eng_sel = st.selectbox("Selecione seu nome:", list(EQUIPE.keys()))
        st.markdown(f'<img src="{EQUIPE[eng_sel]["foto"]}" class="profile-pic">', unsafe_allow_html=True)
        
        # Filtro Inteligente de Campi
        campi_permitidos = sorted(EQUIPE[eng_sel]["campi"])
        campus_sel = st.selectbox("Campus da Vistoria:", campi_permitidos)
        
        if st.button("Sair"): st.session_state["login"] = False; st.rerun()

    # Banner Institucional
    st.markdown(f'''
        <div class="main-header">
            <img src="https://cdn-icons-png.flaticon.com/512/4320/4320350.png" width="80" style="margin-right:20px;">
            <div>
                <h1 style="color:#1e4620; margin:0;">Sistema de Inspeção Predial - IFBA</h1>
                <p style="color:#666; margin:0;">Engenharia, Manutenção e Vistorias Técnicas</p>
            </div>
        </div>
    ''', unsafe_allow_html=True)

    st.markdown(f"### 📝 Registro: {campus_sel}")
    
    col1, col2 = st.columns(2)
    with col1:
        edif = st.selectbox("Edificação/Bloco:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Ginásio", "Guarita", "Estacionamento", "Muro", "Biblioteca"], index=None, placeholder="Onde está a patologia?")
        amb = st.selectbox("Ambiente:", ["Sala de aula", "Laboratório", "Sanitário", "Corredor", "Pátio"], index=None, placeholder="Selecione o ambiente")
        comp = st.text_input("Nº ou Complemento:") if amb and ("Sala" in amb or "Laboratório" in amb) else ""
        disc = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()), index=None, placeholder="Selecione a disciplina")

    with col2:
        if disc:
            pat_op = DADOS_TECNICOS[disc]["patologias"]
            pat_sel = st.selectbox("Patologia Comum:", pat_op, index=None, placeholder="Selecione ou use 'Outros'")
            # Se for "Outros", o campo de texto fica em branco para preencher
            desc_val = "" if pat_sel == "Outros" else (pat_sel if pat_sel else "")
            desc_final = st.text_area("Descrição Técnica Detalhada:", value=desc_val)
            
            sol_op = DADOS_TECNICOS[disc]["solucoes"]
            sol_sel = st.selectbox("Sugestão de Solução:", sol_op, index=None, placeholder="Selecione ou use 'Outros'")
            sol_val = "" if sol_sel == "Outros" else (sol_sel if sol_sel else "")
            sol_final = st.text_area("Proposta de Intervenção:", value=sol_val)
        else:
            st.info("💡 Selecione a Disciplina para carregar as opções.")

    # BLOCO DE FOTO E GUT
    st.markdown("---")
    f1, f2 = st.columns(2)
    with f1:
        st.write("**📸 Evidência Fotográfica**")
        foto_arq = st.file_uploader("Clique para anexar ou tirar foto", type=["jpg", "png", "jpeg"])
    with f2:
        st.write("**Avaliação de Prioridade (GUT)**")
        g = st.select_slider("Gravidade", [1,2,3,4,5], 3)
        u = st.select_slider("Urgência", [1,2,3,4,5], 3)
        t = st.select_slider("Tendência", [1,2,3,4,5], 3)
        score = g*u*t
        status = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
        st.info(f"Prioridade: {status} (Score: {score})")

    if st.button("💾 Salvar Inspeção Completa"):
        st.success(f"Registro de {eng_sel} para o campus {campus_sel} salvo com sucesso!")

    # Rodapé
    st.markdown(f'<div style="text-align:center; color:#888; margin-top:50px; border-top:1px solid #eee; padding-top:20px;">Desenvolvido por: Thiago Messias Carvalho Soares | Roger Ramos Santana<br>Equipe PRODIN - IFBA 2026</div>', unsafe_allow_html=True)
