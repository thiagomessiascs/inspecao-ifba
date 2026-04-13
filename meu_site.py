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

# 🔗 LINK DA PLANILHA
URL_PLANILHA = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"

# 2. SISTEMA DE ACESSO
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acesso Restrito - PRODIN")
    senha = st.text_input("Senha de acesso:", type="password")
    if st.button("Entrar"):
        if senha == "IFBA2026":
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# 3. BANCO DE DADOS TÉCNICO E OPÇÕES
lista_edificacoes = [
    "Pavilhão de Aulas", "Pavilhão Administrativo", "Refeitório", "Ginásio", 
    "Muro", "Estacionamento", "Guarita", "Galpão Industrial", "Usina de Biodiesel", "Usina Solar"
]

lista_ambientes = [
    "Laboratório", "Sala Administrativa", "Sala de Aulas", 
    "Sanitário Masculino", "Sanitário Feminino", "Sanitário PCD", "Outro"
]

sugestoes = {
    "Alvenaria": {"Problemas": ["Fissuras de retração", "Trincas", "Umidade ascendente"], "Soluções": ["Tela de poliéster", "Grampeamento", "Impermeabilização"]},
    "Estrutura": {"Problemas": ["Corrosão de armadura", "Exposição de ferragem", "Bicheiras"], "Soluções": ["Passivação", "Argamassa estrutural", "Grouteamento"]},
    "Pavimentação": {"Problemas": ["Peças soltas", "Buracos", "Desnível"], "Soluções": ["Recomposição", "Tapa-buraco", "Compactação"]},
    "Cobertura": {"Problemas": ["Telhas quebradas", "Calhas obstruídas", "Infiltração"], "Soluções": ["Substituição", "Limpeza", "Vedação PU"]},
    "Revestimento": {"Problemas": ["Descolamento cerâmico", "Descascamento", "Eflorescência"], "Soluções": ["Argamassa AC-III", "Fundo preparador", "Limpeza química"]},
    "Esquadrias": {"Problemas": ["Dificuldade de abrir", "Oxidação", "Vidro quebrado"], "Soluções": ["Lubrificação", "Pintura esmalte", "Troca de vidro"]},
    "Hidráulica": {"Problemas": ["Vazamento", "Baixa pressão", "Pingo em registro"], "Soluções": ["Troca de conexão", "Limpeza de filtros", "Troca de vedante"]},
    "Esgotamento": {"Problemas": ["Mau cheiro", "Entupimento", "Caixa de gordura cheia"], "Soluções": ["Ventilação", "Hidrojateamento", "Limpeza de caixa"]},
    "Drenagem": {"Problemas": ["Acúmulo de água", "Ralo obstruído"], "Soluções": ["Limpeza de grelhas", "Desobstrução"]},
    "Elétrica": {"Problemas": ["Fios expostos", "Quadro s/ identificação", "Disjuntor desarmando"], "Soluções": ["Isolamento", "Identificação", "Equilíbrio de fases"]}
}

lista_disciplinas = ["Escolha..."] + list(sugestoes.keys()) + ["Outras"]

# 4. BARRA LATERAL
st.sidebar.title("⚙️ PRODIN - IFBA")
eng_sel = st.sidebar.selectbox("Engenheiro Responsável", ["Eng. Thiago", "Eng. Roger", "Eng. Laís", "Eng. Larissa", "Eng. Marcelo", "Eng. Fenelon"])
campus_sel = st.sidebar.selectbox("Campus", ["Salvador", "Feira de Santana", "Camaçari", "Vitória da Conquista", "Santo Amaro", "Simões Filho", "Eunápolis"])
choice = st.sidebar.radio("Navegação", ["Nova Inspeção", "Histórico / Gerar PDF"])

# 5. FUNÇÕES
conn = st.connection("gsheets", type=GSheetsConnection)

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RELATÓRIO DE INSPEÇÃO PREDIAL - IFBA", ln=True, align='C')
    pdf.ln(10)
    for k, v in dados.items():
        if k != "Foto_Dados":
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, f"{k}:", 0)
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 8, f"{str(v)}", 0)
    return pdf.output(dest='S').encode('latin-1')

# --- TELA: NOVA INSPEÇÃO ---
if choice == "Nova Inspeção":
    st.header("📋 Registrar Inspeção Técnica")
    
    # INTERATIVIDADE FORA DO FORM
    disciplina = st.selectbox("1. Escolha a Disciplina:", lista_disciplinas)
    
    with st.form("form_final", clear_on_submit=True):
        col_ed, col_dt = st.columns([2, 1])
        with col_ed:
            edificacao = st.selectbox("Edificação / Bloco", lista_edificacoes)
        with col_dt:
            data_ins = st.date_input("Data", datetime.now())

        col_amb, col_num = st.columns([2, 1])
        with col_amb:
            ambiente = st.selectbox("Ambiente / Sala", lista_ambientes)
        with col_num:
            sala_num = st.text_input("Nº da Sala", placeholder="Ex: 102")

        ambiente_completo = f"{ambiente} - {sala_num}" if sala_num else ambiente
        
        descricao = ""
        solucoes_txt = ""

        if disciplina in sugestoes:
            st.divider()
            pat_sel = st.selectbox("Patologia Identificada:", sugestoes[disciplina]["Problemas"])
            descricao = st.text_area("Detalhamento:", value=pat_sel)
            sol_sel = st.selectbox("Solução Sugerida:", sugestoes[disciplina]["Soluções"])
            solucoes_txt = st.text_area("Encaminhamento:", value=sol_sel)
        
        elif disciplina == "Outras":
            descricao = st.text_area("Descreva a Patologia:")
            solucoes_txt = st.text_area("Descreva a Solução:")

        foto = st.file_uploader("📸 Foto da Evidência", type=['jpg', 'jpeg', 'png'])

        if st.form_submit_button("✅ Salvar na Planilha"):
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
                    "Data": data_ins.strftime("%d/%m/%Y"), 
                    "Campus": campus_sel, 
                    "Edificacao": edificacao, 
                    "Disciplina": disciplina, 
                    "Ambiente": ambiente_completo,
                    "Descricao": descricao, 
                    "Solucoes": solucoes_txt, 
                    "Engenheiro": eng_sel, 
                    "Foto_Dados": foto_b64
                }])

                try:
                    df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
                    df_f = pd.concat([df, novo_reg], ignore_index=True)
                    conn.update(spreadsheet=URL_PLANILHA, data=df_f)
                    st.success("✅ Registro salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao conectar com a planilha: {e}")

# --- TELA: HISTÓRICO ---
elif choice == "Histórico / Gerar PDF":
    st.header("📂 Histórico de Registros")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        # Exibir tabela com a data formatada corretamente
        st.dataframe(df.drop(columns=['Foto_Dados'], errors='ignore'), use_container_width=True)
        
        if not df.empty:
            st.divider()
            id_sel = st.selectbox("Selecione para ver detalhes e baixar PDF:", df.index)
            reg = df.iloc[id_sel]
            
            c1, c2 = st.columns([1, 1])
            with c1:
                if reg["Foto_Dados"]:
                    st.image(base64.b64decode(reg["Foto_Dados"]), caption="Evidência")
            with c2:
                st.write(f"**Engenheiro:** {reg['Engenheiro']}")
                st.write(f"**Data:** {reg['Data']}")
                
                pdf_b = gerar_pdf(reg.to_dict())
                st.download_button("📥 Baixar PDF", data=pdf_b, file_name=f"Relatorio_{id_sel}.pdf")
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
