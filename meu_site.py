import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import io
import requests
import base64

# --- 1. CONFIGURAÇÃO DA EQUIPE (PRODIN) ---
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
    },
    "Eng. Laís": {
        "nome_completo": "Lais Sampaio Machado",
        "campi": ["Barreiras", "Jaguaquara", "Jequié"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135823.png"
    },
    "Eng. Larissa": {
        "nome_completo": "Larissa da Silva Oliveira",
        "campi": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacã"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135823.png"
    },
    "Eng. Marcelo": {
        "nome_completo": "Marcelo Souza Almeida",
        "campi": ["Brumado", "Vitória da Conquista"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    },
    "Eng. Fenelon": {
        "nome_completo": "Fenelon Bispo Pereira de Souza",
        "campi": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    },
    "Eng. do Local": {
        "nome_completo": "Engenheiro Responsável do Local",
        "campi": ["Salvador", "Reitoria - Salvador", "Polo de Inovação", "Salinas da Margarida", "São Desidério"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    }
}

# --- 2. FUNÇÃO DE UPLOAD DE FOTO (ImgBB) ---
def upload_para_nuvem(foto_arquivo):
    # Chave de API para o servidor de imagens (Grátis)
    API_KEY = "6908985532588b58a18370126786a347"
    url = "https://api.imgbb.com/1/upload"
    try:
        encoded_image = base64.b64encode(foto_arquivo.read()).decode('utf-8')
        payload = {"key": API_KEY, "image": encoded_image}
        res = requests.post(url, data=payload)
        if res.status_code == 200:
            return res.json()['data']['url']
    except Exception as e:
        st.error(f"Erro no upload da imagem: {e}")
    return ""

# --- 3. GERADOR DE PDF ---
def gerar_pdf_final(df_filtro, campus, eng_nome):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, f"RELATÓRIO DE INSPEÇÃO - IFBA {campus.upper()}", ln=True, align='C')
    pdf.ln(5)
    
    for i, row in df_filtro.iterrows():
        y_pos = pdf.get_y()
        if y_pos > 200: pdf.add_page(); y_pos = pdf.get_y()
        
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(190, 8, f"Item {i+1}: {row['Edificacao']}", ln=True, fill=True)
        
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(110, 6, f"Ambiente: {row['Ambiente']}", ln=True)
        pdf.set_font("Arial", '', 9)
        pdf.multi_cell(110, 5, f"Descrição: {row['Descricao']}")
        pdf.multi_cell(110, 5, f"Soluções: {row['Solucoes']}")
        
        # Insere a foto pela URL salva
        if row['Link_Foto']:
            try:
                img_data = requests.get(row['Link_Foto']).content
                pdf.image(io.BytesIO(img_data), x=125, y=y_pos + 10, w=60)
            except: pass
            
        pdf.set_y(max(pdf.get_y(), y_pos + 60))
        pdf.ln(5)
        pdf.cell(190, 0, '', 'T', ln=True)

    # Assinatura
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "________________________________________________", ln=True, align='C')
    pdf.cell(0, 5, eng_nome, ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. APLICATIVO ---
st.set_page_config(page_title="Inspeção IFBA", layout="wide")

if "autenticado" not in st.session_state: st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    # Tela de Login
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🔐 Acesso Restrito")
        senha = st.text_input("Senha da PRODIN:", type="password")
        if st.button("Entrar"):
            if senha == "IFBA2026": st.session_state["autenticado"] = True; st.rerun()
            else: st.error("Senha inválida")
else:
    # Interface Principal
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(ttl="0")

    with st.sidebar:
        st.header("⚙️ Configuração")
        eng_ativo = st.selectbox("Quem está vistoriando?", list(EQUIPE.keys()))
        campus_sel = st.selectbox("Campus alvo:", sorted(EQUIPE[eng_ativo]["campi"]))
        st.image(EQUIPE[eng_ativo]["foto"], width=100)
        if st.button("Sair"): st.session_state["autenticado"] = False; st.rerun()

    st.title(f"🏗️ Vistoria: {campus_sel}")
    
    with st.form("vistoria_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            bloco = st.text_input("Edificação/Bloco:")
            local = st.text_input("Ambiente:")
            desc = st.text_area("Descrição da Patologia:")
            solu = st.text_area("Sugestão de Solução:")
        with col_b:
            # ESSA LINHA ABAIXO ABRE A CÂMERA NO CELULAR
            foto_cel = st.file_uploader("📸 Tirar Foto Agora", type=["jpg", "png", "jpeg"])
            
            st.write("**Avaliação GUT**")
            g = st.select_slider("Gravidade", options=[1,2,3,4,5], value=3)
            u = st.select_slider("Urgência", options=[1,2,3,4,5], value=3)
            t = st.select_slider("Tendência", options=[1,2,3,4,5], value=3)
            score = g * u * t
            status = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
            st.info(f"Prioridade: {status}")

        if st.form_submit_button("💾 Salvar Registro e Foto"):
            if bloco and desc:
                link_foto = ""
                if foto_cel:
                    with st.spinner("Enviando foto para a nuvem..."):
                        link_foto = upload_para_nuvem(foto_cel)
                
                novo_dado = {
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Engenheiro": eng_ativo,
                    "Campus": campus_sel,
                    "Edificacao": bloco,
                    "Ambiente": local,
                    "Descricao": desc,
                    "Solucoes": solu,
                    "Link_Foto": link_foto, # Link eterno
                    "Score_GUT": score,
                    "Status": status
                }
                df_up = pd.concat([df_base, pd.DataFrame([novo_dado])], ignore_index=True)
                conn.update(data=df_up)
                st.success("Tudo salvo com segurança!")
            else: st.error("Preencha Bloco e Descrição!")

    # SEÇÃO DE RELATÓRIO FINAL POR CAMPUS
    st.write("---")
    df_campus = df_base[df_base['Campus'] == campus_sel]
    if not df_campus.empty:
        st.subheader(f"Resumo do Campus ({len(df_campus)} itens)")
        st.dataframe(df_campus[["Edificacao", "Ambiente", "Status"]], use_container_width=True)
        
        if st.button(f"🏁 Finalizar e Gerar PDF de {campus_sel}"):
            pdf_data = gerar_pdf_final(df_campus, campus_sel, EQUIPE[eng_ativo]["nome_completo"])
            st.download_button("📥 Baixar Relatório Completo", pdf_data, f"Relatorio_{campus_sel}.pdf")
