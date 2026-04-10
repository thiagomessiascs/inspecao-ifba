import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io
import requests
import base64

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

# --- 2. FUNÇÕES DE SUPORTE ---
def upload_imgbb(arquivo):
    API_KEY = "6908985532588b58a18370126786a347"
    try:
        img_b64 = base64.b64encode(arquivo.read()).decode('utf-8')
        res = requests.post("https://api.imgbb.com/1/upload", data={"key": API_KEY, "image": img_b64})
        return res.json()['data']['url'] if res.status_code == 200 else ""
    except: return ""

# --- 3. INTERFACE ---
st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide")

if "login" not in st.session_state: st.session_state["login"] = False

if not st.session_state["login"]:
    st.title("🔐 Login PRODIN")
    if st.text_input("Senha:", type="password") == "IFBA2026":
        if st.button("Acessar"): st.session_state["login"] = True; st.rerun()
else:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(ttl="0")

    with st.sidebar:
        st.subheader("🕵️ Vistoriador")
        eng_sel = st.selectbox("Selecione seu nome:", list(EQUIPE.keys()))
        st.image(EQUIPE[eng_sel]["foto"], width=100)
        campi_permitidos = sorted(EQUIPE[eng_sel]["campi"])
        campus_sel = st.selectbox("Campus da Vistoria:", campi_permitidos)
        if st.button("Sair"): st.session_state["login"] = False; st.rerun()

    # Banner Profissional
    st.markdown(f'<h1 style="color:#1e4620;">🏢 Sistema de Inspeção Predial - IFBA</h1>', unsafe_allow_html=True)
    st.markdown(f"### 📝 Novo Registro: {campus_sel}")
    
    # Colunas de entrada com limpeza automática via key/rerun
    col1, col2 = st.columns(2)
    with col1:
        edif = st.selectbox("Edificação/Bloco:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Guarita", "Biblioteca"], index=None, key="edif_key")
        amb_base = st.selectbox("Ambiente:", ["Sala de aula", "Laboratório", "Sanitário", "Corredor"], index=None, key="amb_key")
        comp = st.text_input("Nº ou Complemento:", key="comp_key") if amb_base and ("Sala" in amb_base or "Laboratório" in amb_base) else ""
        disc = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()), index=None, key="disc_key")

    with col2:
        if disc:
            pat_sel = st.selectbox("Patologia Comum:", DADOS_TECNICOS[disc]["patologias"], index=None, key="pat_key")
            desc_val = "" if pat_sel == "Outros" else (pat_sel if pat_sel else "")
            desc_f = st.text_area("Descrição Técnica:", value=desc_val, key="desc_area_key")
            
            sol_sel = st.selectbox("Sugestão de Solução:", DADOS_TECNICOS[disc]["solucoes"], index=None, key="sol_key")
            sol_val = "" if sol_sel == "Outros" else (sol_sel if sol_sel else "")
            sol_f = st.text_area("Proposta de Intervenção:", value=sol_val, key="sol_area_key")
        else:
            st.info("💡 Escolha a Disciplina para habilitar as patologias.")
            desc_f = sol_f = ""

    st.markdown("---")
    f1, f2 = st.columns(2)
    with f1:
        foto_arq = st.file_uploader("📸 Registro Fotográfico", type=["jpg", "png", "jpeg"], key="foto_key")
    with f2:
        st.write("**Avaliação de Prioridade (GUT)**")
        g = st.select_slider("Gravidade", [1,2,3,4,5], 3, key="g_key")
        u = st.select_slider("Urgência", [1,2,3,4,5], 3, key="u_key")
        t = st.select_slider("Tendência", [1,2,3,4,5], 3, key="t_key")
        score = g*u*t
        st.info(f"Prioridade: {'CRÍTICA' if score > 60 else 'BAIXA'} (Score: {score})")

    # Botão de Salvar com Limpeza de Cache
    if st.button("💾 Salvar Inspeção"):
        if edif and disc:
            with st.spinner("Salvando no histórico..."):
                link = upload_imgbb(foto_arq) if foto_arq else ""
                nova_linha = {
                    "Data": datetime.now().strftime("%d/%m/%Y"), "Engenheiro": eng_sel, 
                    "Campus": campus_sel, "Edificacao": edif, "Ambiente": f"{amb_base} {comp}", 
                    "Disciplina": disc, "Descricao": desc_f, "Solucoes": sol_f, 
                    "Link_Foto": link, "Score_GUT": score, "Status": "CRÍTICA" if score > 60 else "BAIXA"
                }
                df_atualizado = pd.concat([df_base, pd.DataFrame([nova_linha])], ignore_index=True)
                conn.update(data=df_atualizado)
                st.success("✅ Registro gravado! Campos limpos para a próxima inserção.")
                # O rerun limpa todos os widgets que possuem 'key'
                st.rerun()
        else:
            st.error("Preencha os campos obrigatórios (Edificação e Disciplina).")

    # Resumo visual para conferência
    st.markdown("---")
    df_res = df_base[df_base['Campus'] == campus_sel]
    if not df_res.empty:
        st.subheader(f"📋 Itens já registrados em {campus_sel}")
        st.dataframe(df_res[["Edificacao", "Ambiente", "Disciplina", "Score_GUT"]].tail(5), use_container_width=True)

    st.markdown(f'<div style="text-align:center; color:#888; padding-top:20px;">Desenvolvido por: Thiago Messias Carvalho Soares | Roger Ramos Santana<br>Equipe PRODIN - IFBA 2026</div>', unsafe_allow_html=True)
