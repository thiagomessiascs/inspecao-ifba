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

# 🔗 LINK DA PLANILHA (Certifique-se de que as colunas batem com o DataFrame abaixo)
URL_PLANILHA = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"

# 2. SISTEMA DE ACESSO
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acesso Restrito - PRODIN")
    senha = st.text_input("Digite a senha de acesso:", type="password")
    if st.button("Entrar"):
        if senha == "IFBA2026":
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# 3. BANCO DE DADOS TÉCNICO
mapa_engenheiros = {
    "Eng. Thiago": "M", "Eng. Roger": "M", "Eng. Laís": "F", 
    "Eng. Larissa": "F", "Eng. Marcelo": "M", "Eng. Fenelon": "M"
}

sugestoes = {
    "Alvenaria": {
        "Problemas": ["Fissuras de retração", "Trincas estruturais", "Umidade ascendente (rodapé)", "Eflorescência em tijolos"],
        "Soluções": ["Tratamento com tela de poliéster e selante", "Grampeamento e reforço", "Impermeabilização com argamassa polimérica", "Limpeza química e hidrofugação"]
    },
    "Estrutura": {
        "Problemas": ["Corrosão de armaduras", "Exposição de ferragem", "Segregação do concreto (bicheiras)", "Flechas excessivas"],
        "Soluções": ["Escovamento e passivação de ferragem", "Reparo com argamassa estrutural", "Grouteamento", "Escoramento e reforço estrutural"]
    },
    "Pavimentação": {
        "Problemas": ["Peças soltas", "Buracos/Panelas no asfalto", "Desnível acentuado", "Meio-fio quebrado"],
        "Soluções": ["Recomposição de colchão de areia", "Tapa-buraco/Recapeamento", "Compactação de base", "Substituição de guias"]
    },
    "Cobertura": {
        "Problemas": ["Telhas quebradas/deslocadas", "Calhas obstruídas", "Infiltração em rufos", "Estrutura avariada"],
        "Soluções": ["Substituição e fixação", "Limpeza e pintura anticorrosiva", "Vedação com selante PU", "Tratamento de elementos estruturais"]
    },
    "Revestimento": {
        "Problemas": ["Descolamento de cerâmica (som cavo)", "Descascamento de pintura", "Reboco esfarelando"],
        "Soluções": ["Novo assentamento com argamassa AC-III", "Raspagem e nova pintura", "Remoção e novo reboco"]
    },
    "Esquadrias": {
        "Problemas": ["Dificuldade de fechamento", "Oxidação metálica", "Vidros trincados"],
        "Soluções": ["Lubrificação e ajuste de prumo", "Lixamento e pintura esmalte", "Substituição de vidros e silicone"]
    },
    "Hidráulica": {
        "Problemas": ["Vazamento aparente", "Baixa pressão", "Registros pingando"],
        "Soluções": ["Substituição de conexões", "Limpeza de filtros/tubulações", "Troca de vedantes (reparos)"]
    },
    "Esgotamento": {
        "Problemas": ["Retorno de mau cheiro", "Entupimento de ramais", "Caixa de gordura cheia"],
        "Soluções": ["Verificação de sifões/ventilação", "Hidrojateamento", "Limpeza periódica da caixa"]
    },
    "Drenagem": {
        "Problemas": ["Acúmulo de águas pluviais", "Ralos obstruídos", "Caixas de areia cheias"],
        "Soluções": ["Limpeza de grelhas", "Desobstrução de ramais", "Limpeza de caixas de inspeção"]
    },
    "Elétrica": {
        "Problemas": ["Fios expostos", "Quadro sem identificação", "Disjuntores desarmando"],
        "Soluções": ["Isolamento em eletrodutos", "Identificação de circuitos", "Equilíbrio de fases/Troca de disjuntor"]
    }
}

lista_disciplinas = ["Escolha..."] + list(sugestoes.keys()) + ["Outras"]

# 4. BARRA LATERAL
st.sidebar.title("⚙️ Painel de Controle")
eng_sel = st.sidebar.selectbox("Engenheiro Responsável", list(mapa_engenheiros.keys()))

genero = mapa_engenheiros[eng_sel]
avatar = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png" if genero == "M" else "https://cdn-icons-png.flaticon.com/512/219/219969.png"
st.sidebar.image(avatar, width=100)

campus_sel = st.sidebar.selectbox("Campus", ["Salvador", "Feira de Santana", "Camaçari", "Vitória da Conquista", "Santo Amaro", "Simões Filho", "Eunápolis"])
choice = st.sidebar.radio("Navegação", ["Nova Inspeção", "Histórico / Gerar PDF"])

# 5. CONEXÃO E PDF
conn = st.connection("gsheets", type=GSheetsConnection)

def exportar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RELATÓRIO DE INSPEÇÃO PREDIAL - IFBA", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    for k, v in dados.items():
        if k != "Foto_Dados":
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, f"{k}:", 0)
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 8, f"{str(v)}", 0)
            pdf.ln(2)
    return pdf.output(dest='S').encode('latin-1')

# --- TELA: NOVA INSPEÇÃO ---
if choice == "Nova Inspeção":
    st.header("📋 Registrar Nova Inspeção")
    
    # Campo fora do form para interatividade automática
    disciplina = st.selectbox("1. Escolha a Disciplina Técnica:", lista_disciplinas)
    
    with st.form("form_prodin", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            edificacao = st.text_input("Edificação / Bloco")
            ambiente = st.text_input("Ambiente / Sala")
        with col2:
            data_ins = st.date_input("Data da Inspeção", datetime.now())
        
        descricao = ""
        solucoes_txt = ""

        # Lógica de Botões Automáticos
        if disciplina in sugestoes:
            st.markdown(f"---")
            st.info(f"Sugestões para {disciplina}")
            pat_sel = st.selectbox("Selecione a Patologia Identificada:", sugestoes[disciplina]["Problemas"])
            descricao = st.text_area("Detalhamento da Patologia:", value=pat_sel)
            
            sol_sel = st.selectbox("Selecione a Solução Recomendada:", sugestoes[disciplina]["Soluções"])
            solucoes_txt = st.text_area("Sugestão de Encaminhamento:", value=sol_sel)
        
        elif disciplina == "Outras":
            descricao = st.text_area("Descreva a Patologia:")
            solucoes_txt = st.text_area("Descreva a Solução Sugerida:")

        foto = st.file_uploader("📸 Foto da Evidência", type=['jpg', 'jpeg', 'png'])

        if st.form_submit_button("✅ Salvar Inspeção"):
            if disciplina == "Escolha...":
                st.error("Selecione a disciplina!")
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
                    "Disciplina": disciplina, "Ambiente": ambiente, "Descricao": descricao, "Solucoes": solucoes_txt,
                    "Engenheiro": eng_sel, "Foto_Dados": foto_b64
                }])

                try:
                    df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
                    df_f = pd.concat([df, novo_reg], ignore_index=True)
                    conn.update(spreadsheet=URL_PLANILHA, data=df_f)
                    st.success("✅ Registro salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# --- TELA: HISTÓRICO ---
elif choice == "Histórico / Gerar PDF":
    st.header("📂 Histórico de Registros")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        st.dataframe(df.drop(columns=['Foto_Dados'], errors='ignore'), use_container_width=True)
        
        if not df.empty:
            st.divider()
            id_sel = st.selectbox("Selecione o Registro para Detalhes:", df.index)
            reg = df.iloc[id_sel]
            
            c1, c2 = st.columns([1, 1])
            with c1:
                if reg["Foto_Dados"]:
                    st.image(base64.b64decode(reg["Foto_Dados"]), caption="Evidência Fotográfica")
            with c2:
                st.write(f"**Engenheiro:** {reg['Engenheiro']}")
                st.write(f"**Problema:** {reg['Descricao']}")
                
                pdf_bytes = exportar_pdf(reg.to_dict())
                st.download_button("📥 Baixar Relatório em PDF", data=pdf_bytes, file_name=f"Relatorio_{id_sel}.pdf")
    except:
        st.error("Erro ao carregar banco de dados.")

# --- RODAPÉ CENTRALIZADO ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: gray; font-size: 1.1em;">
        <strong>Desenvolvido por:</strong><br>
        Thiago Messias Carvalho Soares & Roger Ramos Santana<br>
        <strong style="color: #2e7d32;">PRODIN - IFBA 2026</strong>
    </div>
    """,
    unsafe_allow_html=True
)
