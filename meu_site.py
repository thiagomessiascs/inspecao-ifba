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

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1i2-Sd9853TrdgUGSo9QRX5sKD7kFmsbuqih9FlF-7F8/edit"
NOME_ABA = "Sheet1" 
URL_LOGO_IFBA = "https://raw.githubusercontent.com/thiagomessiascs/inspecao-ifba/main/logo_ifba_vertical.png"
NOME_ARQUIVO_LOGO = "logo_ifba.png"

# --- DICIONÁRIO COMPLETO DE PATOLOGIAS E SOLUÇÕES ---
sugestoes = {
    'Alvenaria': {
        'Problemas': ['Fissuras de retração térmica', 'Trincas em diagonal (recalque)', 'Umidade por capilaridade (rodapé)', 'Eflorescência', 'Descolamento de emboço/reboco', 'Fissuras em juntas de dilatação'],
        'Soluções': ['Tratamento com tela de poliéster e selante', 'Grampeamento com barras de aço e graute', 'Impermeabilização polimérica de rodapé', 'Limpeza química e hidrofugação', 'Remoção e recomposição de argamassa']
    },
    'Estrutura': {
        'Problemas': ['Corrosão de armaduras (ferro exposto)', 'Fissuras estruturais em vigas/pilares', 'Segregação do concreto (ninhos)', 'Flechas excessivas em lajes', 'Carbonatação do concreto', 'Desagregação por ataque químico'],
        'Soluções': ['Escovamento, passivação e reparo com graute', 'Injeção de resina epóxi', 'Estancamento com argamassa estrutural', 'Reforço com fibra de carbono ou chapas metálicas', 'Pintura de proteção anticarbonatação']
    },
    'Cobertura': {
        'Problemas': ['Telhas quebradas ou fissuradas', 'Calhas obstruídas ou com corrosão', 'Infiltração em rufos e contra-rufos', 'Oxidação em estrutura metálica', 'Deformação em tesouras de madeira', 'Pontos de gotejamento generalizado'],
        'Soluções': ['Substituição de peças danificadas', 'Limpeza e aplicação de pintura betuminosa', 'Vedação com PU 40 e manta aluminizada', 'Lixamento e pintura anticorrosiva (fundo/acabamento)', 'Substituição ou reforço de elementos estruturais']
    },
    'Hidráulica': {
        'Problemas': ['Vazamento aparente em conexões', 'Baixa pressão terminal', 'Obstrução em ramais de esgoto', 'Infiltração por falha em impermeabilização', 'Caixa d\'água com fissuras', 'Retorno de odores por falta de fecho hídrico'],
        'Soluções': ['Substituição de tubulações/conexões', 'Instalação de pressurizador ou limpeza de filtros', 'Desobstrução mecânica e revisão de caixas de inspeção', 'Refação de manta asfáltica/polimérica', 'Reparo interno com argamassa impermeável']
    },
    'Elétrica': {
        'Problemas': ['Fios expostos ou sem isolamento', 'Quadro de energia sem identificação', 'Disjuntores superaquecidos', 'Falta de aterramento (choques)', 'Ausência de dispositivos DR/DPS', 'Luminárias com reator avariado'],
        'Soluções': ['Acondicionamento em eletrodutos e canaletas', 'Etiquetagem e diagramação de circuitos', 'Redimensionamento de carga e troca de componentes', 'Instalação de hastes de aterramento e malha', 'Adequação à NBR 5410 com DR e DPS']
    },
    'Impermeabilização': {
        'Problemas': ['Infiltração em lajes expostas', 'Bolhas em mantas asfálticas', 'Umidade em reservatórios', 'Juntas de dilatação degradadas'],
        'Soluções': ['Aplicação de nova camada impermeabilizante', 'Reparo localizado com maçarico e primer', 'Cristalização de reservatórios', 'Substituição de mastique e delimitador de profundidade']
    }
}

class RelatorioIFBA(FPDF):
    def header(self):
        try:
            if os.path.exists(NOME_ARQUIVO_LOGO):
                self.image(NOME_ARQUIVO_LOGO, x=87, y=10, w=35)
        except: pass
        self.ln(45)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def criar_capa(self, campus, engenheiro):
        self.add_page()
        self.set_font('Arial', 'B', 20)
        self.ln(40)
        self.cell(0, 20, "RELATÓRIO DE VISTORIA TÉCNICA", ln=True, align='C')
        self.set_font('Arial', '', 14)
        self.cell(0, 10, f"CAMPUS: {campus.upper()}", ln=True, align='C')
        self.ln(60)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f"Responsável: {engenheiro}", ln=True, align='C')
        self.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')

    def adicionar_secao(self, titulo, conteudo):
        self.add_page()
        self.set_font('Arial', 'B', 16)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 12, titulo, ln=True, fill=True)
        self.ln(5)
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 8, conteudo)
        self.ln(5)

def gerar_pdf_completo(dados):
    pdf = RelatorioIFBA()
    pdf.criar_capa(dados['Campus'], dados['Engenheiro'])
    intro_txt = (f"Este documento apresenta o registro da vistoria técnica realizada no IFBA Campus {dados['Campus']}. "
                 f"O objetivo é diagnosticar patologias e propor soluções técnicas para a manutenção da edificação {dados['Edificacao']}.")
    pdf.adicionar_secao("1. INTRODUÇÃO", intro_txt)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 12, "2. DADOS DA INSPEÇÃO", ln=True)
    pdf.ln(5)
    for k, v in dados.items():
        if k not in ["Foto_Dados", "Campus", "Engenheiro"]:
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(40, 8, f"{k}:", 1)
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 8, f" {str(v)}", 1)
    if dados.get("Foto_Dados"):
        try:
            img_byte = base64.b64decode(dados["Foto_Dados"])
            img_io = io.BytesIO(img_byte)
            pdf.ln(5)
            pdf.image(img_io, x=45, w=120)
        except: pass
    conclusao_txt = (f"Com base na análise da disciplina {dados['Disciplina']}, recomenda-se seguir os encaminhamentos "
                     f"propostos na seção de 'Soluções' deste relatório para garantir a integridade da edificação.")
    pdf.adicionar_secao("3. CONCLUSÃO E RECOMENDAÇÕES", conclusao_txt)
    return pdf.output(dest='S').encode('latin-1', 'replace')

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

# 3. MAPEAMENTO DE CAMPI
dados_prodin = {
    "Eng. Thiago": {"campi": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"]},
    "Eng. Roger": {"campi": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"]},
    "Eng. Laís": {"campi": ["Barreiras", "Jaguaquara", "Jequié"]},
    "Eng. Larissa": {"campi": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacan"]},
    "Eng. Marcelo": {"campi": ["Brumado", "Vitória da Conquista"]},
    "Eng. Fenelon": {"campi": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"]}
}

conn = st.connection("gsheets", type=GSheetsConnection)

with st.sidebar:
    st.title("⚙️ PRODIN")
    eng_sel = st.selectbox("Engenheiro", list(dados_prodin.keys()))
    campus_sel = st.selectbox("Campus", dados_prodin[eng_sel]["campi"])
    nav = st.radio("Ir para:", ["Nova Inspeção", "Histórico"])

if nav == "Nova Inspeção":
    st.header(f"📋 Nova Inspeção - {campus_sel}")
    
    disc_escolhida = st.selectbox("Disciplina Técnica", ["Escolha..."] + list(sugestoes.keys()))

    with st.form("form_inspecao", clear_on_submit=True):
        c1, c2 = st.columns([1, 1])
        
        edificacao = c1.selectbox("Edificação", [
            "Pavilhão de aulas", "Pavilhão acadêmico", "Pavilhão administrativo", 
            "Ginásio", "Refeitório", "Muro", "Estacionamento", 
            "Usina solar", "Usina de biodiesel", "Guarita"
        ])
        
        ambiente_sel = c2.selectbox("Ambiente", [
            "Sanitário Masculino", "Sanitário Masculino PDC", "Sanitário Feminino", 
            "Sanitário Feminino PDC", "Sala de aula", "Sala ADM", "Depósito", 
            "Laboratório", "Auditório", "Área externa", "Circulação", 
            "Pátio", "Corredor", "Passeio"
        ])
        
        c3, c4 = st.columns([1, 1])
        data_ins = c3.date_input("Data", datetime.now())
        modalidade = c4.selectbox("Modalidade", ["Serviços contínuos", "Serviços eventuais", "Obras ou reformas"])

        prob_sugestao = sugestoes[disc_escolhida]['Problemas'] if disc_escolhida in sugestoes else [""]
        sol_sugestao = sugestoes[disc_escolhida]['Soluções'] if disc_escolhida in sugestoes else [""]
        
        patologia_sel = st.selectbox("Patologia Identificada (Sugestão)", prob_sugestao)
        sol_sel = st.selectbox("Solução Técnica", sol_sugestao)
        
        # ALTERADO: Campo Observações agora inicia em branco
        obs_final = st.text_area("Observações:", value="")
        
        foto = st.file_uploader("📸 Foto da Patologia", type=['jpg', 'png', 'jpeg'])

        if st.form_submit_button("✅ Salvar Inspeção"):
            f_b64 = ""
            if foto:
                img = Image.open(foto).convert("RGB")
                img.thumbnail((600, 600))
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=75)
                f_b64 = base64.b64encode(buf.getvalue()).decode()
            
            reg = {
                "Data": data_ins.strftime("%d/%m/%Y"), "Campus": campus_sel, 
                "Edificacao": edificacao, "Disciplina": disc_escolhida, "Ambiente": ambiente_sel, 
                "Sala": "N/A", "Modalidade": modalidade, "Descricao": patologia_sel, 
                "Solucoes": obs_final, "Engenheiro": eng_sel, "Foto_Dados": f_b64
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
        st.download_button("📥 Baixar PDF do Relatório", 
                           data=gerar_pdf_completo(st.session_state['ultimo_relatorio']), 
                           file_name=f"Inspecao_{campus_sel}.pdf")

elif nav == "Histórico":
    st.header(f"📂 Histórico: {campus_sel}")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet=NOME_ABA, ttl=0)
        st.dataframe(df[df['Campus'] == campus_sel].drop(columns=['Foto_Dados'], errors='ignore'))
    except:
        st.warning("Histórico indisponível.")

st.markdown("<hr><center>Desenvolvido por: Thiago Messias Carvalho Soares & Roger Ramos Santana | PRODIN 2026</center>", unsafe_allow_html=True)
