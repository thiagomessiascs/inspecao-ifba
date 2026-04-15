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

# 🔗 CONFIGURAÇÕES DE CONEXÃO
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1i2-Sd9853TrdgUGSo9QRX5sKD7kFmsbuqih9FlF-7F8/edit"
NOME_ABA = "Sheet1" 
URL_LOGO_IFBA = "https://raw.githubusercontent.com/thiagomessiascs/inspecao-ifba/main/logo_ifba_vertical.png"
NOME_ARQUIVO_LOGO = "logo_ifba.png"

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

# 3. MAPEAMENTO TÉCNICO
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

# 4. FUNÇÃO PDF (SUPORTE A MÚLTIPLAS PÁGINAS PARA HISTÓRICO)
def gerar_pdf(lista_dados, titulo_relatorio="RELATÓRIO DE FISCALIZAÇÃO"):
    pdf = FPDF()
    
    if isinstance(lista_dados, dict):
        lista_dados = [lista_dados]

    for dados in lista_dados:
        pdf.add_page()
        try:
            if not os.path.exists(NOME_ARQUIVO_LOGO):
                r = requests.get(URL_LOGO_IFBA, timeout=5)
                if r.status_code == 200:
                    with open(NOME_ARQUIVO_LOGO, "wb") as f:
                        f.write(r.content)
            pdf.image(NOME_ARQUIVO_LOGO, x=87, y=10, w=35)
        except: pass
            
        pdf.set_y(55)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, titulo_relatorio, ln=True, align='C')
        pdf.set_font("Arial", 'I', 9)
        pdf.cell(190, 5, f"Documento integrante do acervo PRODIN - IFBA", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_fill_color(240, 240, 240)
        colunas_texto = {
            "Data": dados.get("Data"),
            "Campus": dados.get("Campus"),
            "Engenheiro": dados.get("Engenheiro"),
            "Edificação": dados.get("Edificacao"),
            "Local": f"{dados.get('Ambiente')} / {dados.get('Sala')}",
            "Disciplina": dados.get("Disciplina"),
            "Modalidade": dados.get("Modalidade")
        }

        for label, valor in colunas_texto.items():
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(45, 7, f" {label}:", 1, 0, 'L', True)
            pdf.set_font("Arial", '', 9)
            pdf.cell(145, 7, f" {valor}", 1, 1, 'L')

        pdf.ln(5)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(190, 7, " Detalhamento da Ocorrência:", 1, 1, 'L', True)
        pdf.set_font("Arial", '', 9)
        pdf.multi_cell(190, 6, f" {dados.get('Descricao')}", 1, 'L')

        pdf.ln(2)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(190, 7, " Encaminhamentos:", 1, 1, 'L', True)
        pdf.set_font("Arial", '', 9)
        pdf.multi_cell(190, 6, f" {dados.get('Solucoes')}", 1, 'L')

        if dados.get("Foto_Dados"):
            try:
                pdf.ln(5)
                img_byte = base64.b64decode(dados["Foto_Dados"])
                img_io = io.BytesIO(img_byte)
                pdf.image(img_io, x=55, w=100)
            except: pass

    return pdf.output(dest='S').encode('latin-1', 'replace')

# 5. CONEXÃO
conn = st.connection("gsheets", type=GSheetsConnection)

with st.sidebar:
    st.title("⚙️ PRODIN")
    eng_sel = st.selectbox("Engenheiro", list(dados_prodin.keys()))
    campus_sel = st.selectbox("Campus", dados_prodin[eng_sel]["campi"])
    nav = st.radio("Ir para:", ["Nova Inspeção", "Histórico"])

if nav == "Nova Inspeção":
    st.header(f"📋 Nova Inspeção - {campus_sel}")
    disc = st.selectbox("Disciplina Técnica", lista_disciplinas)
    
    with st.form("form_inspecao", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        # --- OPÇÕES DE AMBIENTE ATUALIZADAS ---
        edificacao = c1.selectbox("Edificação", [
            "Pavilhão de aulas", "Pavilhão acadêmico", "Pavilhão administrativo", 
            "Ginásio", "Refeitório", "Muro", "Estacionamento", 
            "Usina solar", "Usina de biodiesel", "Guarita"
        ])
        data_ins = c2.date_input("Data", datetime.now())
        c3, c4 = st.columns([2, 1])
        ambiente = c3.text_input("Ambiente")
        sala = c4.text_input("Sala")
        modalidade = st.selectbox("Modalidade", lista_modalidades)
        desc = st.text_area("Detalhamento:", value=sugestoes[disc]['Problemas'][0] if disc in sugestoes else "")
        sol = st.text_area("Encaminhamento:", value=sugestoes[disc]['Soluções'][0] if disc in sugestoes else "")
        foto = st.file_uploader("📸 Foto", type=['jpg', 'png', 'jpeg'])

        if st.form_submit_button("✅ Salvar Inspeção"):
            f_b64 = ""
            if foto:
                img = Image.open(foto).convert("RGB")
                img.thumbnail((800, 800))
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=75)
                f_b64 = base64.b64encode(buf.getvalue()).decode()
            
            reg = {
                "Data": data_ins.strftime("%d/%m/%Y"), "Campus": campus_sel, 
                "Edificacao": edificacao, "Disciplina": disc, "Ambiente": ambiente, 
                "Sala": sala, "Modalidade": modalidade, "Descricao": desc, 
                "Solucoes": sol, "Engenheiro": eng_sel, "Foto_Dados": f_b64
            }
            
            try:
                df_atual = conn.read(spreadsheet=URL_PLANILHA, worksheet=NOME_ABA, ttl=0)
                df_novo = pd.concat([df_atual, pd.DataFrame([reg])], ignore_index=True)
                conn.update(spreadsheet=URL_PLANILHA, worksheet=NOME_ABA, data=df_novo)
                st.success("✅ Salvo com sucesso!")
                st.session_state['ultimo_relatorio'] = reg
            except Exception as e:
                st.error(f"Erro: {e}")

    if 'ultimo_relatorio' in st.session_state:
        st.download_button("📥 Baixar PDF da Última Inspeção", 
                           data=gerar_pdf(st.session_state['ultimo_relatorio']), 
                           file_name=f"Inspecao_{campus_sel}.pdf")

elif nav == "Histórico":
    st.header(f"📂 Histórico Completo: {campus_sel}")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet=NOME_ABA, ttl=0)
        filtro = df[df['Campus'] == campus_sel]
        
        if not filtro.empty:
            st.write(f"Total de registros encontrados: {len(filtro)}")
            lista_historico = filtro.to_dict('records')
            pdf_historico = gerar_pdf(lista_historico, titulo_relatorio=f"HISTÓRICO DE PATOLOGIAS - {campus_sel.upper()}")
            
            st.download_button(
                label="📥 BAIXAR HISTÓRICO COMPLETO (PDF)",
                data=pdf_historico,
                file_name=f"Historico_Patologias_{campus_sel}.pdf",
                mime="application/pdf"
            )
            
            st.divider()
            st.dataframe(filtro.drop(columns=['Foto_Dados'], errors='ignore'))
        else:
            st.info("Nenhuma patologia registrada para este campus ainda.")
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")

st.markdown("<hr><center>Desenvolvido por: Thiago Messias Carvalho Soares & Roger Ramos Santana | PRODIN 2026</center>", unsafe_allow_html=True)
