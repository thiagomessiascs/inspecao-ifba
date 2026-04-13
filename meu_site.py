import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from PIL import Image
import io
from fpdf import FPDF

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Sistema PRODIN - IFBA", layout="centered", page_icon="📋")

# 🔗 LINK DA SUA PLANILHA (Certifique-se de que a coluna 'Foto_Dados' existe)
URL_PLANILHA = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"

# 2. SISTEMA DE ACESSO
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acesso Restrito - PRODIN")
    senha = st.text_input("Senha:", type="password")
    if st.button("Entrar"):
        if senha == "IFBA2026":
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# 3. BANCO DE DADOS DE SUGESTÕES (PATOLOGIAS E SOLUÇÕES)
mapa_engenheiros = {
    "Eng. Thiago": "M", "Eng. Roger": "M", "Eng. Laís": "F", 
    "Eng. Larissa": "F", "Eng. Marcelo": "M", "Eng. Fenelon": "M", "Eng. do Local": "M"
}

mapa_campi = {
    "Eng. Thiago": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"],
    "Eng. Roger": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"],
    "Eng. Laís": ["Barreiras", "Jaguaquara", "Jequié"],
    "Eng. Larissa": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacã"],
    "Eng. Marcelo": ["Brumado", "Vitória da Conquista"],
    "Eng. Fenelon": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"],
    "Eng. do Local": ["Salvador", "Reitoria", "Polo de Inovação", "Salinas da Margarida", "São Desidério"]
}

sugestoes = {
    "Civil": {
        "Problemas": ["Infiltração em laje/cobertura", "Fissuras em alvenaria", "Piso quebrado/solto", "Pintura descascando/com bolhas", "Porta/Janela com defeito"],
        "Soluções": ["Impermeabilização da superfície", "Tratamento de fissuras e reboco", "Substituição do revestimento", "Repintura com fundo preparador", "Manutenção ou troca da esquadria"]
    },
    "Elétrica": {
        "Problemas": ["Quadro elétrico sem identificação", "Fios expostos", "Tomada/Interruptor danificado", "Iluminação inoperante", "Disjuntor desarmando"],
        "Soluções": ["Identificação e diagrama do quadro", "Isolamento e embutimento de fiação", "Troca da tomada/interruptor", "Substituição de lâmpada/reator", "Revisão da carga e substituição do disjuntor"]
    },
    "Hidráulica": {
        "Problemas": ["Vazamento em tubulação", "Torneira pingando", "Descarga acoplada sem funcionar", "Ralo entupido", "Falta de pressão de água"],
        "Soluções": ["Localização e reparo da tubulação", "Troca do reparo da torneira", "Manutenção ou substituição do mecanismo da descarga", "Desentupimento e limpeza do ralo", "Limpeza do castelo d'água ou pressurização"]
    }
}

# 4. BARRA LATERAL (SIDEBAR)
st.sidebar.title("⚙️ Painel de Controle")
eng_sel = st.sidebar.selectbox("Engenheiro Responsável", list(mapa_engenheiros.keys()))

# Avatar Dinâmico
genero = mapa_engenheiros[eng_sel]
avatar = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png" if genero == "M" else "https://cdn-icons-png.flaticon.com/512/219/219969.png"
st.sidebar.image(avatar, width=100)

campus_sel = st.sidebar.selectbox("Campus", mapa_campi[eng_sel])
choice = st.sidebar.radio("Navegação", ["Nova Inspeção", "Histórico / Gerar PDF"])

# 5. FUNÇÕES AUXILIARES (PDF)
def exportar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RELATÓRIO DE INSPEÇÃO PREDIAL - IFBA", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for chave, valor in dados.items():
        if chave != "Foto_Dados":
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, f"{chave}:", 0)
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 8, f"{valor}", 0)
    return pdf.output(dest='S').encode('latin-1')

# 6. CONEXÃO COM O GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

# --- TELA: NOVA INSPEÇÃO ---
if choice == "Nova Inspeção":
    st.header("📋 Registrar Inspeção")
    
    with st.form("form_inspecao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            edificacao = st.text_input("Edificação / Bloco")
            disciplina = st.selectbox("Selecione a Disciplina", ["Escolha...", "Civil", "Elétrica", "Hidráulica", "Outros"])
        with col2:
            data_ins = st.date_input("Data", datetime.now())
            ambiente = st.text_input("Ambiente / Sala")

        # LOGICA DINÂMICA: Aparece apenas se disciplina for selecionada
        descricao = ""
        solucoes = ""
        
        if disciplina != "Escolha..." and disciplina != "Outros":
            st.markdown("---")
            st.subheader(f"🛠️ Opções para {disciplina}")
            
            # Botões (Selectbox) de Patologias
            patologia_sel = st.selectbox("Selecione a Patologia Identificada:", sugestoes[disciplina]["Problemas"])
            descricao = st.text_area("Descrição detalhada da Não Conformidade:", value=patologia_sel)
            
            # Botões (Selectbox) de Soluções
            solucao_sel = st.selectbox("Selecione a Sugestão de Solução:", sugestoes[disciplina]["Soluções"])
            solucoes = st.text_area("Sugestão de Solução / Encaminhamento:", value=solucao_sel)
        
        elif disciplina == "Outros":
            descricao = st.text_area("Descreva a Patologia:")
            solucoes = st.text_area("Sugestão de Solução:")

        foto = st.file_uploader("📸 Foto (Tirada agora ou Galeria)", type=['jpg', 'jpeg', 'png'])

        if st.form_submit_button("✅ Salvar na Planilha"):
            if disciplina == "Escolha...":
                st.warning("Por favor, selecione uma disciplina primeiro!")
            else:
                foto_b64 = ""
                if foto:
                    img = Image.open(foto)
                    img.thumbnail((700, 700))
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=70)
                    foto_b64 = base64.b64encode(buf.getvalue()).decode()

                novo_reg = pd.DataFrame([{
                    "Data": data_ins.strftime("%d/%m/%Y"), "Campus": campus_sel, "Edificacao": edificacao,
                    "Disciplina": disciplina, "Ambiente": ambiente, "Descricao": descricao, "Solucoes": solucoes,
                    "Engenheiro": eng_sel, "Foto_Dados": foto_b64
                }])

                try:
                    df_atual = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
                    df_final = pd.concat([df_atual, novo_reg], ignore_index=True)
                    conn.update(spreadsheet=URL_PLANILHA, data=df_final)
                    st.success("✅ Registro salvo com sucesso! A foto está na sua galeria e no sistema.")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# --- TELA: HISTÓRICO E PDF ---
elif choice == "Histórico / Gerar PDF":
    st.header("📂 Histórico de Inspeções")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        st.dataframe(df.drop(columns=['Foto_Dados'], errors='ignore'), use_container_width=True)
        
        if not df.empty:
            st.divider()
            id_sel = st.selectbox("Selecione um registro para ver detalhes ou baixar PDF:", df.index)
            reg = df.iloc[id_sel]
            
            c1, c2 = st.columns([1, 1])
            with c1:
                if reg["Foto_Dados"]:
                    st.image(base64.b64decode(reg["Foto_Dados"]), caption="Evidência Fotográfica")
            with c2:
                st.write(f"**Engenheiro:** {reg['Engenheiro']}")
                st.write(f"**Problema:** {reg['Descricao']}")
                
                # Gerador de PDF
                pdf_data = exportar_pdf(reg.to_dict())
                st.download_button(label="📥 Baixar Relatório em PDF", data=pdf_data, 
                                 file_name=f"Inspecao_{reg['Campus']}_{id_sel}.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

# --- RODAPÉ CENTRALIZADO NA PÁGINA ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #6d6d6d; font-size: 1em; line-height: 1.5;">
        <strong>Desenvolvido por:</strong><br>
        Thiago Messias Carvalho Soares & Roger Ramos Santana<br>
        <strong style="color: #2e7d32;">PRODIN - IFBA 2026</strong>
    </div>
    """,
    unsafe_allow_html=True
)
