import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from PIL import Image
import io
from fpdf import FPDF
import requests
import os

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Sistema PRODIN - IFBA", layout="centered", page_icon="📋")

# 🔗 CONFIGURAÇÕES DE LINKS - ATUALIZADO PARA A NOVA PLANILHA NO PRODINEMCAMPUS
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1i2-Sd9853TrdgUGso9QRX5sKD7kFmsbuqih9FIF-7F8/edit#gid=0"
URL_LOGO_IFBA = "https://portal.ifba.edu.br/dgcom/documentos-e-manuais-arquivos/manuais/ifba_marca_vertical-01.png/@@download/file/IFBA_MARCA_vertical-01.png"
NOME_ARQUIVO_LOGO = "logo_ifba_vertical.png"

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

# 3. MAPEAMENTO TÉCNICO E PATOLOGIAS
dados_prodin = {
    "Eng. Thiago": {"campi": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"]},
    "Eng. Roger": {"campi": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"]},
    "Eng. Laís": {"campi": ["Barreiras", "Jaguaquara", "Jequié"]},
    "Eng. Larissa": {"campi": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacan"]},
    "Eng. Marcelo": {"campi": ["Brumado", "Vitória da Conquista"]},
    "Eng. Fenelon": {"campi": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"]}
}

sugestoes = {
    'Alvenaria': {
        'Problemas': ['Fissuras de retração térmica', 'Trincas em diagonal', 'Umidade por capilaridade', 'Eflorescência', 'Descolamento de argamassa'],
        'Soluções': ['Tratamento com tela de poliéster', 'Grampeamento com barras de aço', 'Impermeabilização polimérica', 'Limpeza química']
    },
    'Estrutura': {
        'Problemas': ['Corrosão de armaduras', 'Exposição de ferragem oxidada', 'Segregação do concreto', 'Flechas excessivas'],
        'Soluções': ['Escovamento e passivação', 'Tratamento anticorrosivo', 'Grauteamento estrutural', 'Reforço com fibra de carbono']
    },
    'Cobertura': {
        'Problemas': ['Telhas quebradas/fissuradas', 'Calhas obstruídas', 'Infiltração em rufos', 'Oxidação em estrutura metálica'],
        'Soluções': ['Substituição de peças', 'Limpeza e desobstrução', 'Vedação com PU 40', 'Pintura anticorrosiva']
    },
    'Hidráulica': {
        'Problemas': ['Vazamento aparente', 'Baixa pressão', 'Umidade em paredes', 'Bóia com defeito'],
        'Soluções': ['Substituição de conexões', 'Limpeza de filtros', 'Reparo pontual', 'Troca de vedantes']
    },
    'Elétrica': {
        'Problemas': ['Fios expostos', 'Quadro sem identificação', 'Disjuntores desarmando', 'Falta de aterramento'],
        'Soluções': ['Acondicionamento em eletrodutos', 'Etiquetagem de circuitos', 'Redimensionamento de carga', 'Instalação de DR']
    }
}

lista_disciplinas = ["Escolha..."] + list(sugestoes.keys()) + ["Outras"]
lista_modalidades = ["Serviços contínuos", "Serviços eventuais", "Obras ou reformas"]

# 4. FUNÇÃO PDF
def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    if not os.path.exists(NOME_ARQUIVO_LOGO):
        try: res = requests.get(URL_LOGO_IFBA); open(NOME_ARQUIVO_LOGO, "wb").write(res.content)
        except: pass
    
    if os.path.exists(NOME_ARQUIVO_LOGO): pdf.image(NOME_ARQUIVO_LOGO, x=87, y=15, w=35) 
    pdf.set_y(60)
    pdf.set_font("Arial", 'B', 16); pdf.cell(190, 10, "RELATÓRIO DE FISCALIZAÇÃO - IFBA", ln=True, align='C')
    pdf.set_font("Arial", '', 12); pdf.cell(190, 8, f"Campus: {dados.get('Campus')}", ln=True, align='C')
    pdf.ln(10)
    
    for k, v in dados.items():
        if k != "Foto_Dados":
            pdf.set_font("Arial", 'B', 10); pdf.cell(45, 8, f"{k}:", 1)
            pdf.set_font("Arial", '', 10); pdf.multi_cell(0, 8, f" {str(v)}", 1)
    
    if dados.get("Foto_Dados"):
        try:
            img_data = base64.b64decode(dados["Foto_Dados"])
            pdf.ln(5); pdf.image(io.BytesIO(img_data), x=50, w=110)
        except: pass
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# 5. INTERFACE E CONEXÃO
conn = st.connection("gsheets", type=GSheetsConnection)

with st.sidebar:
    st.title("⚙️ PRODIN")
    eng_sel = st.selectbox("Engenheiro", list(dados_prodin.keys()))
    campus_sel = st.selectbox("Campus", dados_prodin[eng_sel]["campi"])
    nav = st.radio("Ir para:", ["Nova Inspeção", "Histórico"])

if nav == "Nova Inspeção":
    st.header(f"📋 Nova Inspeção - {campus_sel}")
    disc = st.selectbox("Disciplina Técnica", lista_disciplinas)
    
    with st.form("form_inspecao", clear_on_submit=False):
        c1, c2 = st.columns([2, 1])
        edificacao = c1.selectbox("Edificação", ["Pavilhão Aulas", "Adm", "Ginásio", "Refeitório", "Outro"])
        data_ins = c2.date_input("Data", datetime.now())
        
        c3, c4 = st.columns([2, 1])
        ambiente = c3.text_input("Ambiente")
        sala = c4.text_input("Sala")
        
        modalidade = st.selectbox("Modalidade", lista_modalidades)
        
        desc, sol = "", ""
        if disc in sugestoes:
            pat = st.selectbox("Patologia:", sugestoes[disc]['Problemas'])
            desc = st.text_area("Detalhamento:", value=pat)
            sug = st.selectbox("Solução:", sugestoes[disc]['Soluções'])
            sol = st.text_area("Encaminhamento:", value=sug)
        else:
            desc = st.text_area("Detalhamento:")
            sol = st.text_area("Encaminhamento:")
            
        foto = st.file_uploader("📸 Foto", type=['jpg', 'png'])

        if st.form_submit_button("✅ Salvar Inspeção"):
            f_b64 = ""
            if foto:
                img = Image.open(foto); img.thumbnail((600, 600))
                buf = io.BytesIO(); img.save(buf, format="JPEG", quality=70)
                f_b64 = base64.b64encode(buf.getvalue()).decode()
            
            # DICIONÁRIO EXATAMENTE IGUAL AOS CABEÇALHOS DA PLANILHA
            reg = {
                "Data": data_ins.strftime("%d/%m/%Y"), 
                "Campus": campus_sel, 
                "Edificacao": edificacao,
                "Disciplina": disc, 
                "Ambiente": ambiente, 
                "Sala": sala, 
                "Modalidade": modalidade,
                "Descricao": desc, 
                "Solucoes": sol, 
                "Engenheiro": eng_sel, 
                "Foto_Dados": f_b64
            }
            
            try:
                # 1. TENTA LER A PLANILHA (Aba Página1)
                df = conn.read(spreadsheet=URL_PLANILHA, worksheet="Página1", ttl=0)
                
                # 2. CRIA O NOVO DATAFRAME COM O REGISTRO
                novo_reg_df = pd.DataFrame([reg])
                
                # 3. CONCATENA E ATUALIZA
                df_atualizado = pd.concat([df, novo_reg_df], ignore_index=True)
                conn.update(spreadsheet=URL_PLANILHA, worksheet="Página1", data=df_atualizado)
                
                st.success("✅ Inspeção salva com sucesso na planilha do IFBA!")
                st.session_state['ultimo'] = reg
            except Exception as e:
                st.error(f"❌ Erro ao salvar: Verifique se a conta prodin-uploader@... é EDITOR da planilha. Erro: {e}")

    if 'ultimo' in st.session_state:
        st.download_button("📥 Baixar PDF", data=gerar_pdf(st.session_state['ultimo']), file_name=f"Relatorio_{campus_sel}.pdf")

elif nav == "Histórico":
    st.header(f"📂 Histórico: {campus_sel}")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet="Página1", ttl=0)
        df_f = df[df['Campus'] == campus_sel]
        if not df_f.empty:
            st.dataframe(df_f.drop(columns=['Foto_Dados'], errors='ignore'))
        else:
            st.info("Nenhum registro encontrado para este campus.")
    except:
        st.warning("Não foi possível carregar os dados. Verifique a conexão com o Google Sheets.")

st.markdown("<hr><center>Desenvolvido por: Thiago Messias Carvalho Soares & Roger Ramos Santana | PRODIN 2026</center>", unsafe_allow_html=True)
