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

# --- DICIONÁRIO TÉCNICO COMPLETO E DETALHADO ---
sugestoes_v2 = {
    'Alvenaria': {
        'Fissuras de retração térmica': {
            'solucao': 'Tratamento com tela de poliéster e selante elastomérico',
            'obs': 'Procedimento: Abrir a fissura em "V", limpar, aplicar fundo preparador, preencher com selante PU e cobrir com tela de poliéster antes do acabamento.'
        },
        'Umidade por capilaridade (rodapé)': {
            'solucao': 'Impermeabilização polimérica de rodapé',
            'obs': 'Procedimento: Remover reboco até 50cm de altura, aplicar argamassa impermeabilizante estrutural (3 demãos) e refazer o reboco com aditivo hidrófugo.'
        },
        'Eflorescência (sais brancos)': {
            'solucao': 'Limpeza ácida e hidrofugação',
            'obs': 'Procedimento: Escovar a área seca, lavar com solução de ácido clorídrico diluído, enxaguar e, após secagem, aplicar hidrofugante.'
        },
        'Descolamento de revestimento cerâmico': {
            'solucao': 'Substituição de peças com argamassa AC-III',
            'obs': 'Procedimento: Remover peças soltas, limpar o substrato, aplicar argamassa AC-III com técnica de dupla camada e rejuntar.'
        },
        'Fissura em junta de prumada (encontro viga/alvenaria)': {
            'solucao': 'Instalação de tela metálica/eletrosoldada',
            'obs': 'Procedimento: Remover reboco na junta, fixar tela metálica galvanizada cruzando a união viga-alvenaria e aplicar novo chapisco e emboço.'
        }
    },
    'Estrutura': {
        'Corrosão de armaduras (ferro exposto)': {
            'solucao': 'Escovamento, passivação e reparo com graute',
            'obs': 'Procedimento: Remover concreto degradado, limpar armadura com escova de aço, aplicar inibidor de corrosão e recompor com graute estrutural.'
        },
        'Segregação do concreto (bicheiras)': {
            'solucao': 'Preenchimento com graute de alta fluidez',
            'obs': 'Procedimento: Remover partes soltas, lavar a cavidade, aplicar ponte de aderência e preencher com graute estrutural.'
        },
        'Fissura estrutural em viga (tração)': {
            'solucao': 'Injeção de resina epóxi de baixa viscosidade',
            'obs': 'Procedimento: Colocação de bicos injetores, selagem superficial da fissura e injeção de epóxi sob pressão controlada para restabelecer a monoliticidade.'
        },
        'Desagregação do concreto por ataque químico': {
            'solucao': 'Tratamento de superfície e pintura protetora',
            'obs': 'Procedimento: Remover camadas friáveis, estruturalmente comprometidas, neutralizar o substrato, recompor seção com argamassa de reparo e aplicar selador epóxi.'
        }
    },
    'Cobertura': {
        'Infiltração em rufos e contra-rufos': {
            'solucao': 'Vedação com PU 40 e manta aluminizada',
            'obs': 'Procedimento: Limpar o substrato, remover selantes antigos, aplicar cordão de PU 40 nas juntas e reforçar com fita aluminizada.'
        },
        'Obstrução de calhas e condutores': {
            'solucao': 'Limpeza mecânica e revisão de caimentos',
            'obs': 'Procedimento: Remover detritos e sedimentos, testar vazão com água e ajustar suportes se houver empoçamento.'
        },
        'Oxidação em estrutura metálica': {
            'solucao': 'Tratamento anticorrosivo e pintura esmalte',
            'obs': 'Procedimento: Lixamento mecânico (ST3), aplicação de fundo convertedor de ferrugem e acabamento com tinta esmalte sintético.'
        },
        'Telhas cerâmicas/fibrocimento quebradas': {
            'solucao': 'Substituição imediata de elementos de cobertura',
            'obs': 'Procedimento: Identificar peças avariadas, substituir por novas de mesma geometria e revisar a fixação/sobreposição lateral.'
        }
    },
    'Hidráulica': {
        'Vazamento em conexões de PVC': {
            'solucao': 'Substituição de trecho e vedação plástica',
            'obs': 'Procedimento: Cortar o trecho avariado, instalar luvas de correr ou conexões novas com abraçadeiras apropriadas.'
        },
        'Retorno de odor em ralos e sifões': {
            'solucao': 'Substituição de desconector ou recomposição de fecho hídrico',
            'obs': 'Procedimento: Verificar integridade da caixa sifonada; se necessário, instalar sifão com copo ou aumentar profundidade do fecho hídrico.'
        },
        'Infiltração proveniente de barrilete': {
            'solucao': 'Revisão de boias e flanges de reservatórios',
            'obs': 'Procedimento: Substituir boias mecânicas danificadas, reapertar ou trocar flanges com gaxetas de vedação ressecadas.'
        },
        'Obstrução de ramal de esgoto primário': {
            'solucao': 'Desobstrução mecânica e limpeza de caixas',
            'obs': 'Procedimento: Utilizar sonda mecânica ou hidrojateamento, seguido de limpeza completa das caixas de inspeção a jusante.'
        }
    },
    'Elétrica': {
        'Superaquecimento de disjuntores': {
            'solucao': 'Reaperto de conexões e redimensionamento',
            'obs': 'Procedimento: Verificar torque nos terminais; caso o aquecimento persista, medir corrente e substituir por disjuntor de curva adequada.'
        },
        'Fios expostos ou sem isolamento': {
            'solucao': 'Acondicionamento em eletrodutos e isolamento',
            'obs': 'Procedimento: Desligar o circuito, revisar emendas com fita isolante de alta fusão e organizar a fiação dentro de canaletas/eletrodutos.'
        },
        'Ausência de dispositivo DR (Segurança)': {
            'solucao': 'Instalação de interruptor diferencial residual (IDR)',
            'obs': 'Procedimento: Adequar o quadro de distribuição para instalação do DR de 30mA para proteção contra choques conforme NBR 5410.'
        },
        'Quadro de distribuição sem identificação': {
            'solucao': 'Mapeamento de circuitos e etiquetagem',
            'obs': 'Procedimento: Realizar teste de continuidade, identificar cada circuito e aplicar etiquetas adesivas legíveis no espelho do quadro.'
        }
    },
    'Impermeabilização': {
        'Infiltração em laje exposta': {
            'solucao': 'Aplicação de manta asfáltica ou membrana PU',
            'obs': 'Procedimento: Regularizar piso com caimento de 1%, aplicar primer e fundir manta asfáltica com maçarico (sobreposição 10cm).'
        },
        'Falha em junta de dilatação': {
            'solucao': 'Substituição de mastique e delimitador',
            'obs': 'Procedimento: Remover selante antigo, inserir corpo de apoio (back-rod) e aplicar novo mastique de poliuretano.'
        },
        'Umidade em reservatório inferior/superior': {
            'solucao': 'Impermeabilização com argamassa polimérica cristalizante',
            'obs': 'Procedimento: Esvaziar reservatório, limpar paredes, tratar fissuras com fita telada e aplicar 3 demãos de argamassa polimérica.'
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

# 3. MAPEAMENTO DOS PROFISSIONAIS (HOMEM 👷‍♂️ E MULHER 👷‍♀️)
dados_prodin = {
    "Eng. Thiago": {"campi": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"], "icone": "👷‍♂️"},
    "Eng. Roger": {"campi": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"], "icone": "👷‍♂️"},
    "Eng. Laís": {"campi": ["Barreiras", "Jaguaquara", "Jequié"], "icone": "👷‍♀️"},
    "Eng. Larissa": {"campi": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacan"], "icone": "👷‍♀️"},
    "Eng. Marcelo": {"campi": ["Brumado", "Vitória da Conquista"], "icone": "👷‍♂️"},
    "Eng. Fenelon": {"campi": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"], "icone": "👷‍♂️"}
}

conn = st.connection("gsheets", type=GSheetsConnection)

with st.sidebar:
    st.title("⚙️ PRODIN")
    eng_sel = st.selectbox("Engenheiro", list(dados_prodin.keys()))
    
    # --- CÓDIGO DO ÍCONE CIRCULAR CENTRALIZADO E AMPLIADO ---
    icone_profissional = dados_prodin[eng_sel]["icone"]
    st.markdown(f"""
    <div style="display: flex; justify-content: center; margin-top: 10px; margin-bottom: 25px;">
        <div style="
            width: 125px; 
            height: 125px; 
            background-color: white; 
            border-radius: 50%; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-size: 85px;
            line-height: 1;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.15);
            border: 5px solid #2e7d32;
        ">
            {icone_profissional}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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

        lista_patologias = list(sugestoes_v2[disc_escolhida].keys()) if disc_escolhida in sugestoes_v2 else [""]
        patologia_sel = st.selectbox("Patologia Identificada", lista_patologias)
        
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
