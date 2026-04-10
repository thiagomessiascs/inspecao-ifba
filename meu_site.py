import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import io

# --- 1. CONFIGURAÇÃO DA EQUIPE (PRODIN) ---
EQUIPE = {
    "Eng. Thiago": {
        "campi": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"],
        # Link Raw que você forneceu - Agora vai funcionar!
        "foto": "https://github.com/thiagomessiascs/inspecao-ifba/blob/main/Thiago.jpg?raw=true" 
    },
    "Eng. Roger": {
        "campi": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    },
    "Eng. Laís": {
        "campi": ["Barreiras", "Jaguaquara", "Jequié"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135823.png"
    },
    "Eng. Larissa": {
        "campi": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacã"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135823.png"
    },
    "Eng. Marcelo": {
        "campi": ["Brumado", "Vitória da Conquista"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    },
    "Eng. Fenelon": {
        "campi": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    },
    "Eng. do Local": {
        "campi": ["Salvador", "Reitoria - Salvador", "Polo de Inovação", "Salinas da Margarida", "São Desidério"],
        "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    }
}

# 2. Sistema de Autenticação
def verificar_senha():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if not st.session_state["autenticado"]:
        st.set_page_config(page_title="Login - Inspeção IFBA", page_icon="🔐")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔐 Acesso Restrito")
            st.subheader("Sistema de Inspeção IFBA")
            senha = st.text_input("Digite a senha de acesso:", type="password")
            if st.button("Entrar"):
                if senha == "IFBA2026":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
        return False
    return True

if verificar_senha():
    st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide", page_icon="🏗️")

    # --- CSS PARA FOTO CIRCULAR ---
    st.markdown("""
        <style>
        .profile-pic {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid #2e7d32;
            margin-bottom: 10px;
        }
        .sidebar-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- CABEÇALHO ---
    url_construcao = "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?q=80&w=300&auto=format&fit=crop"
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; background-color: #fcfcfc; padding: 25px; border-radius: 20px; border-left: 12px solid #2e7d32; border-bottom: 2px solid #e0e0e0; margin-bottom: 30px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
            <div style="margin-right: 25px;">
                <img src="{url_construcao}" style="width: 180px; height: 120px; border-radius: 12px; object-fit: cover; border: 1px solid #ddd;">
            </div>
            <div style="flex-grow: 1;">
                <h1 style="margin: 0; color: #1e4620; font-family: sans-serif; font-size: 38px;">Sistema de Inspeção Predial - IFBA</h1>
                <p style="margin: 0; color: #666; font-size: 18px; font-weight: 300;">Engenharia, Manutenção e Vistorias Técnicas</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df_base = conn.read(ttl="0")
        df_base = df_base.reset_index(drop=True)
    except:
        df_base = pd.DataFrame()

    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("👨‍🏫 Vistoriador")
        
        eng_nomes = list(EQUIPE.keys())
        if "eng_ativo" not in st.session_state:
            st.session_state["eng_ativo"] = "Eng. Thiago"
            
        eng_ativo = st.selectbox("Selecione o Engenheiro:", eng_nomes, 
                                 index=eng_nomes.index(st.session_state["eng_ativo"]))
        st.session_state["eng_ativo"] = eng_ativo
        
        # HTML para a foto circular - Agora carregando via URL direta
        st.markdown(f"""
            <div class="sidebar-container">
                <img src="{EQUIPE[eng_ativo]['foto']}" class="profile-pic">
                <p style="font-weight: bold; color: #2e7d32;">{eng_ativo}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.header("🏢 Unidades PRODIN")
        
        # Lista dinâmica de Campi baseada no mapa da PRODIN
        lista_campi_dinamica = sorted(EQUIPE[eng_ativo]["campi"])
        campus_sel = st.selectbox("Selecione o Campus:", lista_campi_dinamica)
        
        st.markdown("---")
        st.subheader("🛠️ Opções")
        
        df_campus = df_base[df_base['Campus'] == campus_sel] if not df_base.empty else pd.DataFrame()
        edit_mode = False
        index_to_edit = None
        dados_edit = None
        
        if not df_campus.empty:
            opcoes_edit = ["Nova Inspeção"] + [f"ID {i} - {row['Edificacao']}" for i, row in df_campus.iterrows()]
            selecao = st.selectbox("Editar Registro:", opcoes_edit)
            if selecao != "Nova Inspeção":
                edit_mode = True
                index_to_edit = int(selecao.split(" ")[1])
                dados_edit = df_base.iloc[index_to_edit]

        if st.button("🚪 Sair do Sistema"):
            st.session_state["autenticado"] = False
            st.rerun()

    # --- FORMULÁRIO PRINCIPAL ---
    with st.form("form_vistoria", clear_on_submit=not edit_mode):
        st.subheader(f"📝 Registro: {campus_sel}")
        st.write(f"Responsável Técnico: **{eng_ativo}**")
        
        c1, c2 = st.columns(2)
        with c1:
            edificacao = st.text_input("Edificação/Bloco:", value=dados_edit['Edificacao'] if edit_mode else "", key="edif")
            disciplina_lista = ["Alvenaria", "Estrutura", "Elétrica", "Hidráulica", "Pintura", "Cobertura", "Drenagem", "Incêndio"]
            idx_disc = disciplina_lista.index(dados_edit['Disciplina']) if edit_mode and dados_edit['Disciplina'] in disciplina_lista else 0
            disciplina = st.selectbox("Disciplina:", disciplina_lista, index=idx_disc)
            ambiente = st.text_input("Ambiente/Local:", value=dados_edit['Ambiente'] if edit_mode else "")
            descricao = st.text_area("Descrição da Patologia:", value=dados_edit['Descricao'] if edit_mode else "")
            solucoes = st.text_area("Soluções Sugeridas:", value=dados_edit['Solucoes'] if edit_mode else "")
            
        with c2:
            st.write("**📸 Evidência Fotográfica**")
            foto_upload = st.file_uploader("Upload da foto", type=["jpg", "png", "jpeg"])
            if foto_upload:
                st.image(Image.open(foto_upload), caption="Prévia da Ocorrência", use_container_width=True)
            
            st.write("**Avaliação GUT**")
            g = st.slider("Gravidade", 1, 5, 3)
            u = st.slider("Urgência", 1, 5, 3)
            t = st.slider("Tendência", 1, 5, 3)
            score = g * u * t
            status = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
            st.metric("Prioridade", status, f"Score: {score}")

        if st.form_submit_button("💾 Salvar Inspeção"):
            nova_linha = {
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Engenheiro": eng_ativo,
                "Campus": campus_sel,
                "Edificacao": edificacao,
                "Disciplina": disciplina,
                "Ambiente": ambiente,
                "Descricao": descricao,
                "Solucoes": solucoes,
                "Foto": "Anexada" if foto_upload else (dados_edit['Foto'] if edit_mode else "Sem foto"),
                "Score_GUT": score,
                "Status": status
            }
            if edit_mode:
                df_base.iloc[index_to_edit] = nova_linha
            else:
                df_base = pd.concat([df_base, pd.DataFrame([nova_linha])], ignore_index=True)
            conn.update(data=df_base)
            st.success("Dados registrados no Google Sheets!")
            st.rerun()

    # --- HISTÓRICO E PDF ---
    if not df_base.empty:
        df_filtrado = df_base[df_base['Campus'] == campus_sel]
        if not df_filtrado.empty:
            st.markdown("---")
            st.subheader(f"📋 Ocorrências - {campus_sel}")
            st.dataframe(df_filtrado.drop(columns=["Campus"]), use_container_width=True)

            def gerar_pdf(dados, campus):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, f"RELATÓRIO DE INSPEÇÃO PREDIAL - IFBA {campus.upper()}", ln=True, align='C')
                pdf.ln(10)
                
                for i, row in dados.iterrows():
                    pdf.set_fill_color(240, 240, 240)
                    pdf.set_font("Arial", 'B', 12)
                    pdf.cell(190, 8, f"Item {i+1}: {row['Edificacao']} - Resp: {row.get('Engenheiro', 'N/A')}", ln=True, fill=True)
                    
                    pdf.set_font("Arial", 'B', 10)
                    pdf.cell(40, 7, "Local/Ambiente:", 0)
                    pdf.set_font("Arial", '', 10)
                    pdf.cell(0, 7, f"{row['Ambiente']}", ln=True)
                    
                    pdf.set_font("Arial", 'B', 10)
                    pdf.multi_cell(0, 7, "Descrição da Patologia:")
                    pdf.set_font("Arial", '', 10)
                    pdf.multi_cell(0, 5, f"{row['Descricao']}")
                    
                    pdf.set_font("Arial", 'B', 10)
                    pdf.multi_cell(0, 7, "Soluções Sugeridas:")
                    pdf.set_font("Arial", '', 10)
                    pdf.multi_cell(0, 5, f"{row['Solucoes']}")
                    
                    pdf.set_font("Arial", 'B', 10)
                    cor_status = (211, 47, 47) if row['Status'] == "CRÍTICA" else (218, 165, 32)
                    pdf.set_text_color(*cor_status)
                    pdf.cell(0, 7, f"PRIORIDADE GUT: {row['Status']} (Score: {row['Score_GUT']})", ln=True)
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(5)
                    pdf.cell(190, 0, '', 'T', ln=True)
                    pdf.ln(5)

                pdf.ln(15)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 10, "________________________________________________", ln=True, align='C')
                # Desenvolvedores: Thiago e Roger Santana
                pdf.cell(0, 5, "Thiago Messias Carvalho Soares | Roger Ramos Santana", ln=True, align='C')
                pdf.set_font("Arial", '', 9)
                pdf.cell(0, 5, "Engenheiros Civis - Equipe PRODIN IFBA", ln=True, align='C')
                
                return pdf.output(dest='S').encode('latin-1', 'ignore')

            pdf_data = gerar_pdf(df_filtrado, campus_sel)
            st.download_button(
                label="📄 Baixar Relatório PDF",
                data=pdf_data,
                file_name=f"Relatorio_{campus_sel}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    # --- RODAPÉ ---
    st.markdown("---")
    st.markdown(
        """
        <div style="background-color: #f1f3f6; padding: 20px; border-radius: 15px; text-align: center;">
            <p style="margin: 0; color: #1e4620; font-weight: bold;">Inspeção Predial IFBA - Sistema PRODIN</p>
            <p style="margin: 5px 0 0 0; color: #555; font-size: 13px;">Desenvolvido por <b>Thiago Messias Carvalho Soares</b> e <b>Roger Ramos Santana</b></p>
        </div>
        """,
        unsafe_allow_html=True
    )
