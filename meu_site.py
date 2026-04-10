import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io
import requests
import base64

# --- 1. BANCO DE DADOS TÉCNICO (HIERARQUIA SOLICITADA) ---
DADOS_TECNICOS = {
    "Alvenaria": {
        "patologias": ["Fissura/Trinca", "Mofo/Umidade", "Desplacamento de reboco", "Eflorescência", "Tijolo aparente"],
        "solucoes": ["Tratamento de fissuras com tela", "Impermeabilização", "Reboco novo", "Limpeza e pintura"]
    },
    "Estrutura": {
        "patologias": ["Corrosão de armadura", "Segregação de concreto", "Fissura estrutural", "Exposição de ferragem"],
        "solucoes": ["Escarificação e tratamento de aço", "Grouteamento", "Reforço estrutural"]
    },
    "Cobertura": {
        "patologias": ["Telha quebrada", "Infiltração em calha", "Goteira", "Estrutura de madeira podre"],
        "solucoes": ["Substituição de telhas", "Limpeza e vedação de calhas", "Revisão do telhado"]
    },
    "Pavimentação": {
        "patologias": ["Piso solto/quebrado", "Desgaste", "Buraco", "Rachadura no piso"],
        "solucoes": ["Substituição de revestimento", "Regularização de base", "Rejuntamento"]
    },
    "Esquadrias": {
        "patologias": ["Vidro quebrado", "Ferrugem", "Dificuldade de fechar", "Falta de vedação"],
        "solucoes": ["Troca de vidro", "Pintura anticorrosiva", "Ajuste/Lubrificação de ferragens"]
    },
    "Instalação elétrica": {
        "patologias": ["Fiação exposta", "Disjuntor desarmando", "Lâmpada queimada", "Tomada danificada"],
        "solucoes": ["Revisão de cabeamento", "Troca de componentes", "Identificação de circuitos"]
    },
    "Instalação hidrossanitária": {
        "patologias": ["Vazamento", "Entupimento", "Mau cheiro", "Torneira pingando"],
        "solucoes": ["Troca de reparo", "Desobstrução", "Revisão de tubulação"]
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

# --- 3. FUNÇÕES DE SUPORTE (PDF E UPLOAD) ---
def upload_para_nuvem(foto_arquivo):
    API_KEY = "6908985532588b58a18370126786a347"
    url = "https://api.imgbb.com/1/upload"
    try:
        encoded_image = base64.b64encode(foto_arquivo.read()).decode('utf-8')
        res = requests.post(url, data={"key": API_KEY, "image": encoded_image})
        return res.json()['data']['url'] if res.status_code == 200 else ""
    except: return ""

def gerar_pdf_final(df_filtro, campus):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, f"RELATÓRIO DE INSPEÇÃO PREDIAL - IFBA {campus.upper()}", ln=True, align='C')
    pdf.ln(5)
    
    for i, row in df_filtro.iterrows():
        y_pos = pdf.get_y()
        if y_pos > 200: pdf.add_page(); y_pos = pdf.get_y()
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(190, 8, f"Item {i+1}: {row['Edificacao']} - {row['Ambiente']}", ln=True, fill=True)
        pdf.set_font("Arial", '', 9)
        info = f"Disciplina: {row['Disciplina']}\nDescrição: {row['Descricao']}\nSoluções: {row['Solucoes']}\nPrioridade: {row['Status']} (Score: {row['Score_GUT']})"
        pdf.multi_cell(110, 5, info)
        if row['Link_Foto']:
            try:
                img_data = requests.get(row['Link_Foto']).content
                pdf.image(io.BytesIO(img_data), x=125, y=y_pos + 10, w=60)
            except: pass
        pdf.set_y(max(pdf.get_y(), y_pos + 60))
        pdf.ln(5)
        pdf.cell(190, 0, '', 'T', ln=True)

    # Assinatura Conjunta
    pdf.ln(20)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "__________________________________________________________________", ln=True, align='C')
    pdf.cell(0, 5, "Thiago Messias Carvalho Soares | Roger Ramos Santana", ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. INTERFACE STREAMLIT ---
st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide")

st.markdown("""
    <style>
    .title-card { border: 2px solid #2e7d32; border-left: 15px solid #2e7d32; padding: 30px; border-radius: 15px; background-color: #fcfcfc; display: flex; align-items: center; justify-content: center; margin-bottom: 30px; }
    .footer { text-align: center; color: #999; font-size: 0.8em; margin-top: 50px; border-top: 1px solid #eee; padding-top: 20px; }
    .profile-pic { width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 3px solid #2e7d32; display: block; margin: 0 auto; }
    </style>
    """, unsafe_allow_html=True)

if "autenticado" not in st.session_state: st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔐 Login PRODIN")
    senha = st.text_input("Senha:", type="password")
    if st.button("Acessar"):
        if senha == "IFBA2026": st.session_state["autenticado"] = True; st.rerun()
else:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(ttl="0")

    with st.sidebar:
        st.markdown(f"### 🕵️ Vistoriador")
        eng_ativo = st.selectbox("Selecione:", list(EQUIPE.keys()))
        st.markdown(f'<img src="{EQUIPE[eng_ativo]["foto"]}" class="profile-pic">', unsafe_allow_html=True)
        campus_sel = st.selectbox("Campus:", sorted(EQUIPE[eng_ativo]["campi"]))
        if st.button("Sair"): st.session_state["autenticado"] = False; st.rerun()

    # Título com Ícone de Edificação
    st.markdown(f"""
        <div class="title-card">
            <span style="font-size: 4em; margin-right: 25px;">🏢</span>
            <div>
                <h1 style="color:#1e4620; margin:0;">Sistema de Inspeção Predial - IFBA</h1>
                <p style="color:#666; margin:0;">Engenharia, Manutenção e Vistorias Técnicas</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"### 📝 Registro de Patologia: {campus_sel}")
    
    with st.form("form_vistoria", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            edificacao = st.selectbox("Edificação/Bloco:", ["Pavilhão administrativo", "Pavilhão acadêmico", "Refeitório", "Anexo", "Ginásio", "Guarita", "Estacionamento", "Passeio", "Muro", "Biblioteca"])
            
            amb_base = st.selectbox("Ambiente:", ["Sala de aula", "Laboratório", "Sanitário PCD", "Sanitário Comum", "Sala administrativa", "Corredor/Pátio"])
            amb_livre = ""
            if "Sala" in amb_base or "Laboratório" in amb_base:
                amb_livre = st.text_input("Nº ou Complemento:", placeholder="Ex: Sala 43")
            
            disciplina = st.selectbox("Disciplina:", list(DADOS_TECNICOS.keys()))
            
        with c2:
            # Hierarquia de Patologia e Solução
            pat_opcoes = DADOS_TECNICOS[disciplina]["patologias"]
            pat_sel = st.selectbox("Patologia Comum:", pat_opcoes)
            desc_final = st.text_area("Descrição Técnica:", value=pat_sel)
            
            sol_opcoes = DADOS_TECNICOS[disciplina]["solucoes"]
            sol_sel = st.selectbox("Solução Sugerida:", sol_opcoes)
            sol_final = st.text_area("Proposta de Intervenção:", value=sol_sel)

        st.markdown("---")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            foto_arq = st.file_uploader("📸 Evidência Fotográfica", type=["jpg", "png", "jpeg"])
        with col_f2:
            st.write("**Matriz GUT**")
            g = st.select_slider("Gravidade (1-5)", options=[1,2,3,4,5], value=3)
            u = st.select_slider("Urgência (1-5)", options=[1,2,3,4,5], value=3)
            t = st.select_slider("Tendência (1-5)", options=[1,2,3,4,5], value=3)
            score = g * u * t
            status = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
            st.info(f"Prioridade: {status} (Score: {score})")

        if st.form_submit_button("💾 Salvar Registro"):
            link = upload_para_nuvem(foto_arq) if foto_arq else ""
            amb_final = f"{amb_base} ({amb_livre})" if amb_livre else amb_base
            nova_linha = {
                "Data": datetime.now().strftime("%d/%m/%Y"), "Engenheiro": eng_ativo, 
                "Campus": campus_sel, "Edificacao": edificacao, "Ambiente": amb_final, 
                "Disciplina": disciplina, "Descricao": desc_final, "Solucoes": sol_final, 
                "Link_Foto": link, "Score_GUT": score, "Status": status
            }
            df_up = pd.concat([df_base, pd.DataFrame([nova_linha])], ignore_index=True)
            conn.update(data=df_up)
            st.success("Salvo com sucesso no Google Sheets!")

    # RESUMO E PDF
    st.markdown("---")
    df_resumo = df_base[df_base['Campus'] == campus_sel]
    if not df_resumo.empty:
        st.subheader(f"📋 Vistorias em {campus_sel}")
        st.dataframe(df_resumo[["Edificacao", "Ambiente", "Status", "Score_GUT"]], use_container_width=True)
        if st.button("🏁 Gerar PDF Final"):
            pdf_bytes = gerar_pdf_final(df_resumo, campus_sel)
            st.download_button("📥 Baixar Relatório Técnico", pdf_bytes, f"Relatorio_{campus_sel}.pdf")

    st.markdown(f'<div class="footer">Desenvolvido por: Thiago Messias Carvalho Soares | Roger Ramos Santana<br>Equipe PRODIN - IFBA 2026</div>', unsafe_allow_html=True)
