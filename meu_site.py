import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io
import requests
import base64

# --- 1. BANCO DE DATA HIERÁRQUICO (DISCIPLINA -> PATOLOGIA -> SOLUÇÃO) ---
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
    "Esquadrias": {
        "patologias": ["Vidro quebrado", "Ferrugem", "Dificuldade de fechamento", "Falta de vedação", "Acessórios danificados"],
        "solucoes": ["Troca de vidro", "Pintura anticorrosiva", "Ajuste/Lubrificação", "Troca de borrachas/escovas"]
    },
    "Instalação elétrica": {
        "patologias": ["Fiação exposta", "Disjuntor desarmando", "Quadro sem identificação", "Lâmpada/Reator queimado"],
        "solucoes": ["Revisão de cabeamento", "Troca de disjuntores", "Identificação de circuitos", "Substituição por LED"]
    },
    "Instalação hidrossanitária": {
        "patologias": ["Vazamento em torneira/válvula", "Entupimento", "Mau cheiro", "Infiltração de esgoto/água"],
        "solucoes": ["Troca de reparo/vedante", "Desobstrução", "Sifonagem adequada", "Revisão de tubulação e conexões"]
    },
    "Outros": {"patologias": ["Especificar no campo livre"], "solucoes": ["Especificar no campo livre"]}
}

# --- 2. CONFIGURAÇÃO DA EQUIPE (PRODIN) ---
EQUIPE = {
    "Eng. Thiago": {
        "nome_completo": "Thiago Messias Carvalho Soares",
        "campi": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"],
        "foto": "https://github.com/thiagomessiascs/inspecao-ifba/blob/main/Thiago.jpg?raw=true" 
    },
    "Eng. Roger": {
        "nome_completo": "Roger Ramos Santana",
        "campi": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    }
}

# --- 3. FUNÇÕES TÉCNICAS (PDF E UPLOAD) ---
def upload_imgbb(arquivo):
    API_KEY = "6908985532588b58a18370126786a347"
    try:
        url = "https://api.imgbb.com/1/upload"
        img_b64 = base64.b64encode(arquivo.read()).decode('utf-8')
        res = requests.post(url, data={"key": API_KEY, "image": img_b64})
        return res.json()['data']['url'] if res.status_code == 200 else ""
    except: return ""

def gerar_pdf(df_filtro, campus):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, f"RELATÓRIO DE INSPEÇÃO PREDIAL - IFBA {campus.upper()}", ln=True, align='C')
    pdf.ln(5)
    for i, row in df_filtro.iterrows():
        y = pdf.get_y()
        if y > 210: pdf.add_page(); y = pdf.get_y()
        pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 11)
        pdf.cell(190, 8, f"Item {i+1}: {row['Edificacao']} - {row['Ambiente']}", ln=True, fill=True)
        pdf.set_font("Arial", '', 9)
        info = f"Disciplina: {row['Disciplina']}\nDescrição: {row['Descricao']}\nSoluções: {row['Solucoes']}\nScore GUT: {row['Score_GUT']} ({row['Status']})"
        pdf.multi_cell(110, 5, info)
        if row['Link_Foto']:
            try:
                img = requests.get(row['Link_Foto']).content
                pdf.image(io.BytesIO(img), x=125, y=y+10, w=60)
            except: pass
        pdf.set_y(max(pdf.get_y(), y + 62)); pdf.ln(5); pdf.cell(190, 0, '', 'T', ln=True)
    pdf.ln(20); pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "__________________________________________________________________", ln=True, align='C')
    pdf.cell(0, 5, "Thiago Messias Carvalho Soares | Roger Ramos Santana", ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. INTERFACE ---
st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide")
st.markdown("""
    <style>
    .title-card { border: 2px solid #2e7d32; border-left: 15px solid #2e7d32; padding: 30px; border-radius: 15px; background-color: #fcfcfc; display: flex; align-items: center; justify-content: center; margin-bottom: 30px; }
    .footer { text-align: center; color: #999; font-size: 0.8em; margin-top: 50px; border-top: 1px solid #eee; padding-top: 20px; }
    .profile-pic { width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 3px solid #2e7d32; display: block; margin: 0 auto; }
    </style>
""", unsafe_allow_html=True)

if "login" not in st.session_state: st.session_state["login"] = False

if not st.session_state["login"]:
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        st.title("🔐 Acesso PRODIN")
        if st.text_input("Senha:", type="password") == "IFBA2026":
            if st.button("Entrar"): st.session_state["login"] = True; st.rerun()
else:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(ttl="0")

    with st.sidebar:
        st.subheader("🕵️ Vistoriador")
        eng = st.selectbox("Selecione:", list(EQUIPE.keys()))
        st.markdown(f'<img src="{EQUIPE[eng]["foto"]}" class="profile-pic">', unsafe_allow_html=True)
        campus = st.selectbox("Campus:", sorted(EQUIPE[eng]["campi"]))
        if st.button("Sair"): st.session_state["login"] = False; st.rerun()

    # Título Principal
    st.markdown(f'<div class="title-card"><span style="font-size: 4em; margin-right: 25px;">🏢</span><div><h1 style="color:#1e4620; margin:0;">Sistema de Inspeção Predial - IFBA</h1><p style="color:#666; margin:0;">Engenharia, Manutenção e Vistorias Técnicas</p></div></div>', unsafe_allow_html=True)

    with st.form("vistoria", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            edif = st.selectbox("Edificação/Bloco:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Ginásio", "Guarita", "Estacionamento", "Passeio", "Muro", "Biblioteca"], index=None, placeholder="Onde você está?")
            amb = st.selectbox("Ambiente:", ["Sala de aula", "Laboratório", "Sanitário PCD", "Sanitário Comum", "Sala administrativa", "Corredor/Pátio"], index=None, placeholder="Selecione o ambiente...")
            complemento = st.text_input("Nº ou Complemento:", placeholder="Ex: Sala 43") if amb and ("Sala" in amb or "Laboratório" in amb) else ""
            disc = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()), index=None, placeholder="Selecione a disciplina...")
        
        with col2:
            if disc:
                pat_sel = st.selectbox("Patologia Comum:", DADOS_TECNICOS[disc]["patologias"], index=None, placeholder="O que encontrou?")
                desc_final = st.text_area("Descrição Técnica:", value=pat_sel if pat_sel else "")
                sol_sel = st.selectbox("Solução Comum:", DADOS_TECNICOS[disc]["solucoes"], index=None, placeholder="Como resolver?")
                sol_final = st.text_area("Proposta de Intervenção:", value=sol_sel if sol_sel else "")
            else:
                st.info("Escolha a Disciplina para ver patologias e soluções.")
                desc_final = sol_final = ""

        st.markdown("---")
        f1, f2 = st.columns(2)
        with f1: foto = st.file_uploader("📸 Evidência Fotográfica", type=["jpg", "png", "jpeg"])
        with f2:
            st.write("**Matriz GUT**")
            g, u, t = st.select_slider("Gravidade", [1,2,3,4,5], 3), st.select_slider("Urgência", [1,2,3,4,5], 3), st.select_slider("Tendência", [1,2,3,4,5], 3)
            score = g*u*t
            status = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
            st.info(f"Prioridade: {status} (Score: {score})")

        if st.form_submit_button("💾 Salvar Registro"):
            if edif and disc:
                link = upload_imgbb(foto) if foto else ""
                nova_linha = {"Data": datetime.now().strftime("%d/%m/%Y"), "Engenheiro": eng, "Campus": campus, "Edificacao": edif, "Ambiente": f"{amb} {complemento}", "Disciplina": disc, "Descricao": desc_final, "Solucoes": sol_final, "Link_Foto": link, "Score_GUT": score, "Status": status}
                df_up = pd.concat([df_base, pd.DataFrame([nova_linha])], ignore_index=True)
                conn.update(data=df_up); st.success("Salvo com sucesso!")
            else: st.error("Campos obrigatórios: Edificação e Disciplina.")

    # RESUMO E PDF
    st.markdown("---")
    df_res = df_base[df_base['Campus'] == campus]
    if not df_res.empty:
        st.subheader(f"📋 Itens de {campus}")
        st.dataframe(df_res[["Edificacao", "Ambiente", "Status", "Score_GUT"]], use_container_width=True)
        if st.button("🏁 Gerar Relatório PDF"):
            st.download_button("📥 Baixar PDF", gerar_pdf(df_res, campus), f"Inspecao_{campus}.pdf")

    st.markdown(f'<div class="footer">Desenvolvido por: Thiago Messias Carvalho Soares | Roger Ramos Santana</div>', unsafe_allow_html=True)
