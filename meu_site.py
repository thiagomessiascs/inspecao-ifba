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

# 🔗 CONFIGURAÇÕES DE LINKS E LOGO OFICIAL
URL_PLANILHA = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"
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

# 3. MAPEAMENTO TÉCNICO E BANCO DE PATOLOGIAS EXPANDIDO
dados_prodin = {
    "Eng. Thiago": {"genero": "M", "campi": ["Euclides da Cunha", "Irecê", "Jacobina", "Seabra", "Monte Santo"]},
    "Eng. Roger": {"genero": "M", "campi": ["Eunápolis", "Feira de Santana", "Paulo Afonso", "Porto Seguro", "Santo Amaro", "Itatim"]},
    "Eng. Laís": {"genero": "F", "campi": ["Barreiras", "Jaguaquara", "Jequié"]},
    "Eng. Larissa": {"genero": "F", "campi": ["Campo Formoso", "Juazeiro", "Casa Nova", "Ilhéus", "Ubaitaba", "Camacan"]},
    "Eng. Marcelo": {"genero": "M", "campi": ["Brumado", "Vitória da Conquista"]},
    "Eng. Fenelon": {"genero": "M", "campi": ["Camaçari", "Lauro de Freitas", "Santo Antônio de Jesus", "Simões Filho", "Valença"]}
}

sugestoes = {
    'Alvenaria': {
        'Problemas': ['Fissuras de retração térmica', 'Trincas em diagonal (esforço estrutural)', 'Umidade por capilaridade (rodapé)', 'Eflorescência (sais brancos)', 'Desaprumo evidente', 'Descolamento de argamassa', 'Fissuras em H (esmagamento)', 'Presença de mofo/bolor', 'Fissuras horizontais (sobrecarga)'],
        'Soluções': ['Tratamento com tela de poliéster e selante', 'Grampeamento com barras de aço', 'Impermeabilização polimérica', 'Limpeza química e hidrofugação', 'Regularização de prumo', 'Tratamento biocida', 'Injeção de resina', 'Reforço estrutural da parede']
    },
    'Estrutura': {
        'Problemas': ['Corrosão de armaduras (expansão)', 'Exposição de ferragem oxidada', 'Segregação do concreto (bicheiras)', 'Flechas excessivas (deformação)', 'Fissuras de cisalhamento em vigas', 'Desagregação por ataque químico', 'Ninhos de concretagem', 'Carbonatação do concreto'],
        'Soluções': ['Escovamento, passivação e recomposição estrutural', 'Tratamento anticorrosivo e grauteamento', 'Limpeza e preenchimento com graute fluido', 'Escoramento e reforço com fibra de carbono', 'Injeção de resina de epóxi', 'Jaquetamento de pilar']
    },
    'Cobertura': {
        'Problemas': ['Telhas quebradas/fissuradas', 'Telhas deslocadas (vento)', 'Calhas obstruídas', 'Corrosão em calhas metálicas', 'Infiltração em rufos', 'Estrutura metálica com oxidação', 'Madeiramento com cupim/podridão', 'Pontos de goteira'],
        'Soluções': ['Substituição das peças avariadas', 'Revisão de fixação', 'Limpeza e desobstrução manual', 'Pintura betuminosa ou troca', 'Substituição de rufos e PU 40', 'Lixamento e pintura anticorrosiva', 'Imunização química']
    },
    'Hidráulica': {
        'Problemas': ['Vazamento aparente em conexões', 'Baixa pressão no sistema', 'Torneiras/Registros pingando', 'Ruído de golpe de aríete', 'Umidade em paredes (invisível)', 'Caixa d\'água com sujidade', 'Bóia com defeito', 'Corrosão em tubulação galvanizada'],
        'Soluções': ['Substituição de conexões/reparos', 'Limpeza de crivos e filtros', 'Troca de vedantes (reparos)', 'Instalação de válvulas de alívio', 'Geofonamento e reparo pontual', 'Limpeza e desinfecção', 'Substituição por PVC/PEX']
    },
    'Elétrica': {
        'Problemas': ['Fios expostos/sem isolamento', 'Quadro sem identificação de circuitos', 'Disjuntores desarmando (sobrecarga)', 'Aquecimento de condutores', 'Falta de aterramento', 'Luminárias piscando/queimadas', 'Tomadas com sinais de centelhamento', 'Falta de dispositivo DR'],
        'Soluções': ['Acondicionamento em eletrodutos', 'Etiquetagem e mapeamento de circuitos', 'Redimensionamento de carga', 'Troca de condutores por seção adequada', 'Instalação de malha de terra', 'Substituição por LED', 'Instalação de DR conforme NBR 5410']
    },
    'Pavimentação': {
        'Problemas': ['Peças soltas/quebradas', 'Buracos (potholes)', 'Desnível por recalque', 'Trincas "couro de jacaré"', 'Meio-fio deslocado', 'Acúmulo de lama/areia', 'Falta de rejuntamento'],
        'Soluções': ['Recomposição de base e travamento', 'Tapa-buraco asfáltico', 'Compactação de base e correção de cota', 'Fresagem e recapeamento', 'Alinhamento de guias', 'Selagem de trincas']
    }
}

lista_disciplinas = ["Escolha..."] + list(sugestoes.keys()) + ["Outras"]
lista_modalidades = ["Serviços contínuos", "Serviços eventuais", "Obras ou reformas"]

# 4. FUNÇÃO PARA GERAR O PDF COMPLETO (PADRÃO OFICIAL PRODIN)
def gerar_pdf(dados):
    campus = dados.get('Campus', 'IFBA')
    data_relatorio = dados.get('Data', datetime.now().strftime("%d/%m/%Y"))
    engenheiro = dados.get('Engenheiro', 'Responsável Técnico')

    if not os.path.exists(NOME_ARQUIVO_LOGO):
        try: res = requests.get(URL_LOGO_IFBA); open(NOME_ARQUIVO_LOGO, "wb").write(res.content)
        except: pass

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PÁGINA 1: CAPA ---
    pdf.add_page()
    if os.path.exists(NOME_ARQUIVO_LOGO): pdf.image(NOME_ARQUIVO_LOGO, x=87, y=15, w=35) 
    pdf.set_y(60)
    pdf.set_font("Arial", 'B', 18); pdf.cell(190, 15, "RELATÓRIO DE FISCALIZAÇÃO", ln=True, align='C')
    pdf.set_font("Arial", '', 12); pdf.cell(190, 8, "RELATÓRIO DE VISITA TÉCNICA - DINFRA/PRODIN/IFBA", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12); pdf.cell(190, 8, f"CAMPUS - {campus.upper()}", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 10, f"Data: {data_relatorio}", ln=True, align='C')
    
    pdf.ln(20); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "ÓRGÃO RESPONSÁVEL – CONTRATANTE", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 5, "IFBA – Instituto Federal de Educação, Ciência e Tecnologia da Bahia", ln=True, align='C')
    pdf.cell(190, 5, "CNPJ: 10.764.307/0001-12 | Reitoria: Salvador - BA", ln=True, align='C')
    
    pdf.ln(20); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 8, "PROGRAMA PRODIN EM CAMPUS", ln=True, align='C')
    pdf.set_font("Arial", '', 11); pdf.cell(190, 6, "Diretoria de Infraestrutura | Departamento de Obras e Fiscalização", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, f"RESPONSÁVEL: {engenheiro.upper()}", ln=True, align='C')

    # --- PÁGINA 2: INTRODUÇÃO ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14); pdf.cell(190, 10, "1. INTRODUÇÃO", ln=True)
    pdf.set_font("Arial", '', 11)
    intro_texto = f"A Diretoria de Infraestrutura (DINFRA) por intermédio do Departamento de Obras e Fiscalização está realizando visitas técnicas nas unidades do Instituto visando o acompanhamento das edificações e infraestrutura por profissionais habilitados. O objetivo geral das visitas é avaliar, observar e analisar as construções identificando patologias e possíveis soluções. A unidade foco deste relatório é o campus {campus}."
    pdf.multi_cell(0, 7, intro_texto)

    # --- PÁGINA 3: DETALHAMENTO ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14); pdf.cell(190, 10, "2. DETALHAMENTO TÉCNICO", ln=True)
    pdf.set_font("Arial", '', 10)
    for k, v in dados.items():
        if k != "Foto_Dados":
            pdf.set_font("Arial", 'B', 10); pdf.cell(45, 8, f"{k}:", 1)
            pdf.set_font("Arial", '', 10); pdf.multi_cell(0, 8, f" {str(v)}", 1)
    
    if dados.get("Foto_Dados"):
        try:
            img_data = base64.b64decode(dados["Foto_Dados"])
            pdf.ln(10); pdf.image(io.BytesIO(img_data), x=45, w=110)
        except: pass

    # --- PÁGINA 4: CONCLUSÃO ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14); pdf.cell(190, 10, "3. CONCLUSÃO", ln=True)
    pdf.set_font("Arial", '', 11)
    concl = "Após a vistoria, a Fiscalização constatou a presença de manifestações patológicas nas edificações. Conclui-se que as ações de manutenção deverão ser implementadas com objetivo de reduzir a degradação e potencializar a vida útil das instalações. A equipe DINFRA permanece à disposição para auxílios necessários."
    pdf.multi_cell(0, 7, concl)
    pdf.ln(20); pdf.cell(190, 10, f"Salvador, {datetime.now().strftime('%d/%m/%Y')}.", ln=True)

    return pdf.output(dest='S').encode('latin-1', 'replace')

# 5. BARRA LATERAL (SIDEBAR)
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>⚙️ PRODIN - IFBA</h1>", unsafe_allow_html=True)
    eng_sel = st.selectbox("Engenheiro Responsável", list(dados_prodin.keys()))
    campus_sel = st.selectbox("Campus", dados_prodin[eng_sel]["campi"])
    st.divider()
    choice = st.radio("Navegação", ["Nova Inspeção", "Histórico / PDF"])

# 6. CONEXÃO COM GOOGLE SHEETS E TELAS
conn = st.connection("gsheets", type=GSheetsConnection)

if choice == "Nova Inspeção":
    st.header(f"📋 Registrar Inspeção Técnica")
    disciplina = st.selectbox("1. Escolha a Disciplina Técnica:", lista_disciplinas)
    
    with st.form("form_prodin_final", clear_on_submit=False):
        col_ed, col_dt = st.columns([2, 1])
        with col_ed: edificacao = st.selectbox("Edificação", ["Pavilhão de Aulas", "Pavilhão Adm", "Refeitório", "Ginásio", "Muro", "Outro"])
        with col_dt: data_ins = st.date_input("Data da Inspeção", datetime.now())
        
        col_amb, col_num = st.columns([2, 1])
        with col_amb: ambiente = st.text_input("Ambiente (Ex: Sala Adm)")
        with col_num: sala_num = st.text_input("Nº Sala")

        modalidade = st.selectbox("Modalidade", lista_modalidades)
        
        desc_final, sol_final = "", ""
        if disciplina in sugestoes:
            st.divider()
            pat_sel = st.selectbox("Patologia Identificada:", sugestoes[disciplina]['Problemas'])
            desc_final = st.text_area("Detalhamento:", value=pat_sel)
            sol_sel = st.selectbox("Solução Sugerida:", sugestoes[disciplina]['Soluções'])
            sol_final = st.text_area("Encaminhamento:", value=sol_sel)
        
        foto = st.file_uploader("📸 Foto da Evidência", type=['jpg', 'jpeg', 'png'])

        if st.form_submit_button("✅ Salvar Inspeção"):
            if disciplina == "Escolha...":
                st.error("Selecione a disciplina!")
            else:
                f_b64 = ""
                if foto:
                    img = Image.open(foto); img.thumbnail((700, 700))
                    buf = io.BytesIO(); img.save(buf, format="JPEG", quality=70)
                    f_b64 = base64.b64encode(buf.getvalue()).decode()
                
                novo_reg = {
                    "Data": data_ins.strftime("%d/%m/%Y"), "Campus": campus_sel, "Edificacao": edificacao, 
                    "Disciplina": disciplina, "Ambiente": ambiente, "Sala": sala_num, "Modalidade": modalidade,
                    "Descricao": desc_final, "Solucoes": sol_final, "Engenheiro": eng_sel, "Foto_Dados": f_b64
                }
                
                try:
                    df_atual = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
                    conn.update(spreadsheet=URL_PLANILHA, data=pd.concat([df_atual, pd.DataFrame([novo_reg])], ignore_index=True))
                    st.success("✅ Inspeção salva com sucesso!")
                    st.session_state['ultimo_rel'] = novo_reg
                except: st.error("Erro ao salvar. Verifique o link da planilha.")

    if 'ultimo_rel' in st.session_state:
        st.divider()
        st.subheader("📄 Ações para o último registro")
        st.download_button("📥 Baixar PDF da Inspeção", data=gerar_pdf(st.session_state['ultimo_rel']), file_name=f"Inspecao_{campus_sel}.pdf", mime="application/pdf")

elif choice == "Histórico / PDF":
    st.header(f"📂 Histórico - Campus {campus_sel}")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        df_f = df[df['Campus'] == campus_sel]
        if df_f.empty:
            st.info(f"Sem registros para {campus_sel}.")
        else:
            st.dataframe(df_f.drop(columns=['Foto_Dados'], errors='ignore'), use_container_width=True)
            id_sel = st.selectbox("Selecione o registro para gerar PDF:", df_f.index)
            st.download_button("📥 Baixar PDF Selecionado", data=gerar_pdf(df_f.loc[id_sel].to_dict()), file_name=f"Relatorio_{campus_sel}_{id_sel}.pdf")
    except: st.error("Erro ao carregar dados.")

# RODAPÉ COM OS DESENVOLVEDORES
st.markdown("<br><hr><div style='text-align: center; color: gray;'><strong>Desenvolvido por:</strong><br>Thiago Messias Carvalho Soares & Roger Ramos Santana<br>PRODIN - IFBA 2026</div>", unsafe_allow_html=True)
