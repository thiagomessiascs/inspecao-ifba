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

# --- DICIONÁRIO ESTRUTURADO (AMARRADO) ---
sugestoes_v2 = {
    'Alvenaria': {
        'Fissuras de retração térmica': {
            'solucao': 'Tratamento com tela de poliéster e selante elastomérico',
            'obs': 'Procedimento: Abrir a fissura em formato de "V", limpar, aplicar fundo preparador, preencher com selante e cobrir com tela de poliéster antes do acabamento.'
        },
        'Umidade por capilaridade (rodapé)': {
            'solucao': 'Impermeabilização polimérica de rodapé',
            'obs': 'Procedimento: Remover o reboco afetado até 50cm acima da mancha, aplicar argamassa impermeabilizante em 3 demãos cruzadas e refazer o emboço com aditivo hidrófugo.'
        }
    },
    'Estrutura': {
        'Corrosão de armaduras (ferro exposto)': {
            'solucao': 'Escovamento, passivação e reparo com graute',
            'obs': 'Procedimento: Delimitar a área, remover concreto degradado, limpar armadura com escova de aço, aplicar inibidor de corrosão e recompor seção com graute estrutural.'
        }
    },
    'Cobertura': {
        'Infiltração em rufos e contra-rufos': {
            'solucao': 'Vedação com PU 40 e manta aluminizada',
            'obs': 'Procedimento: Limpar a superfície do rufo, remover vedações antigas ressecadas, aplicar cordão de PU 40 nas juntas e reforçar com fita aluminizada autocolante.'
        }
    },
    'Hidráulica': {
        'Vazamento aparente em conexões': {
            'solucao': 'Substituição de conexões e vedação',
            'obs': 'Procedimento: Fechar o registro, cortar o trecho avariado, instalar novas conexões com adesivo plástico ou fita veda-rosca e testar estanqueidade.'
        }
    },
    'Elétrica': {
        'Fios expostos ou sem isolamento': {
            'solucao': 'Acondicionamento em eletrodutos e isolamento técnico',
            'obs': 'Procedimento: Desligar o circuito, revisar as emendas com fita isolante de alta fusão e organizar a fiação dentro de canaletas ou eletrodutos normatizados.'
        }
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
    conclusao_txt = (f"Com base na análise da disciplina {dados['Disciplina']}, recomenda-se seguir os encaminhamentos propostos.")
    pdf.adicionar_secao("3. CONCLUSÃO", conclusao_txt)
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
        else: st.error("Senha incorreta!")
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
    
    disc_escolhida = st.selectbox("Disciplina Técnica", ["Escolha..."] + list(sugestoes_v2.keys()))

    with st.form("form_inspecao", clear_on_submit=True):
        c1, c2 = st.columns([1, 1])
        edificacao = c1.selectbox("Edificação", ["Pavilhão de aulas", "Pavilhão acadêmico", "Pavilhão administrativo", "Ginásio", "Refeitório", "Muro", "Estacionamento", "Usina solar", "Usina de biodiesel", "Guarita"])
        ambiente_sel = c2.selectbox("Ambiente", ["Sanitário Masculino", "Sanitário Masculino PDC", "Sanitário Feminino", "Sanitário Feminino PDC", "Sala de aula", "Sala ADM", "Depósito", "Laboratório", "Auditório", "Área externa", "Circulação", "Pátio", "Corredor", "Passeio"])
        
        c3, c4 = st.columns([1, 1])
        data_ins = c3.date_input("Data", datetime.now())
        modalidade = c4.selectbox("Modalidade", ["Serviços contínuos", "Serviços eventuais", "Obras ou reformas"])

        # LÓGICA DE AMARRAÇÃO
        lista_patologias = list(sugestoes_v2[disc_escolhida].keys()) if disc_escolhida in sugestoes_v2 else [""]
        patologia_sel = st.selectbox("Patologia Identificada", lista_patologias)
        
        # Busca automática no dicionário v2
        dados_patologia = sugestoes_v2.get(disc_escolhida, {}).get(patologia_sel, {"solucao": "", "obs": ""})
        
        sol_automatica = st.text_input("Solução Técnica (Automática):", value=dados_patologia['solucao'])
        obs_final = st.text_area("Observações (Procedimento de Execução):", value=dados_patologia['obs'])
        
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
                "Solucoes": f"{sol_automatica} | {obs_final}", "Engenheiro": eng_sel, "Foto_Dados": f_b64
            }
            
            try:
                df_atual = conn.read(spreadsheet=URL_PLANILHA, worksheet=NOME_ABA, ttl=0)
                df_novo = pd.concat([df_atual, pd.DataFrame([reg])], ignore_index=True)
                conn.update(spreadsheet=URL_PLANILHA, worksheet=NOME_ABA, data=df_novo)
                st.success("✅ Salvo com sucesso!")
                st.session_state['ultimo_relatorio'] = reg
            except Exception as e: st.error(f"Erro: {e}")

    if 'ultimo_relatorio' in st.session_state:
        st.download_button("📥 Baixar PDF do Relatório", data=gerar_pdf_completo(st.session_state['ultimo_relatorio']), file_name=f"Inspecao_{campus_sel}.pdf")

elif nav == "Histórico":
    st.header(f"📂 Histórico: {campus_sel}")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet=NOME_ABA, ttl=0)
        st.dataframe(df[df['Campus'] == campus_sel].drop(columns=['Foto_Dados'], errors='ignore'))
    except: st.warning("Histórico indisponível.")

st.markdown("<hr><center>Desenvolvido por: Thiago Messias Carvalho Soares & Roger Ramos Santana | PRODIN 2026</center>", unsafe_allow_html=True)
