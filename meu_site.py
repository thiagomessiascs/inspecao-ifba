import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
from PIL import Image
import io
from fpdf import FPDF
import requests

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Sistema PRODIN - IFBA", layout="centered", page_icon="📋")

# 🔗 IMPORTANTE: COLE O LINK DA SUA PLANILHA ABAIXO
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

# 3. MAPEAMENTO TÉCNICO COMPLETO
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
        'Problemas': [
            'Fissuras de retração térmica', 'Trincas em diagonal (esforço estrutural)', 'Umidade por capilaridade (rodapé)', 
            'Eflorescência (sais brancos)', 'Desaprumo evidente', 'Descolamento de argamassa', 'Fissuras em H (esmagamento)', 
            'Presença de mofo/bolor', 'Furos/Aberturas sem vedação', 'Fissuras horizontais (sobrecarga)', 'Destacamento de blocos'
        ],
        'Soluções': [
            'Tratamento com tela de poliéster e selante', 'Grampeamento com barras de aço', 'Impermeabilização polimérica', 
            'Limpeza química e hidrofugação', 'Regularização de prumo', 'Reforço de vergas', 'Tratamento biocida', 
            'Vedação com espuma expansiva/PU', 'Injeção de resina', 'Reforço estrutural da parede'
        ]
    },
    'Estrutura': {
        'Problemas': [
            'Corrosão de armaduras (expansão)', 'Exposição de ferragem oxidada', 'Segregação do concreto (bicheiras)', 
            'Flechas excessivas (deformação)', 'Fissuras de cisalhamento em vigas', 'Desagregação por ataque químico',
            'Ninhos de concretagem', 'Trincas em pilares', 'Esmagamento de apoio', 'Carbonatação do concreto'
        ],
        'Soluções': [
            'Escovamento, passivação e recomposição estrutural', 'Tratamento anticorrosivo e grauteamento', 
            'Limpeza e preenchimento com graute fluido', 'Escoramento e reforço com fibra de carbono', 'Injeção de resina de epóxi', 
            'Remoção de concreto degradado', 'Reparo tixotrópico', 'Jaquetamento de pilar', 'Aumento de seção'
        ]
    },
    'Pavimentação': {
        'Problemas': [
            'Peças soltas/quebradas', 'Buracos/Panelas (potholes)', 'Desnível por recalque', 'Trincas couro de jacaré', 
            'Exsudação de ligante', 'Meio-fio deslocado', 'Acúmulo de lama/areia', 'Falta de rejuntamento', 'Afundamento de trilha'
        ],
        'Soluções': [
            'Recomposição de base e travamento', 'Tapa-buraco asfáltico', 'Compactação de base e correção de cota', 
            'Fresagem e recapeamento', 'Aplicação de agregados', 'Alinhamento de guias', 'Limpeza e varredura', 'Selagem de trincas'
        ]
    },
    'Cobertura': {
        'Problemas': [
            'Telhas quebradas/fissuradas', 'Telhas deslocadas (vento)', 'Calhas obstruídas', 'Corrosão em calhas metálicas', 
            'Infiltração em rufos', 'Estrutura metálica com oxidação', 'Madeiramento com cupim/podridão', 'Pontos de goteira'
        ],
        'Soluções': [
            'Substituição das peças avariadas', 'Revisão de fixação', 'Limpeza e desobstrução manual', 
            'Pintura betuminosa ou troca', 'Substituição de rufos e PU 40', 'Lixamento e pintura anticorrosiva', 'Imunização química'
        ]
    },
    'Revestimento': {
        'Problemas': [
            'Descolamento cerâmico (som cavo)', 'Eflorescência em rejuntes', 'Descascamento/Bolhas na pintura', 
            'Reboco esfarelando', 'Fissuras mapeadas (teia de aranha)', 'Cerâmica trincada', 'Mofo excessivo'
        ],
        'Soluções': [
            'Novo assentamento com AC-III', 'Limpeza ácida e rejunte impermeável', 'Raspagem, fundo preparador e repintura', 
            'Remoção total e novo reboco com aditivo', 'Selador e massa acrílica', 'Troca da peça cerâmica', 'Limpeza com cloro'
        ]
    },
    'Esquadrias': {
        'Problemas': [
            'Dificuldade de deslize', 'Oxidação em marcos metálicos', 'Vidros quebrados/soltos', 'Falta de vedação', 
            'Braços de articulação travados', 'Fechaduras com defeito', 'Infiltração pela guarnição'
        ],
        'Soluções': [
            'Limpeza e lubrificação de roldanas', 'Tratamento de corrosão e pintura esmalte', 'Troca de vidros e silicone', 
            'Novas guarnições/escovas', 'Substituição de ferragens', 'Troca do miolo', 'Vedação externa com PU'
        ]
    },
    'Hidráulica': {
        'Problemas': [
            'Vazamento aparente em conexões', 'Baixa pressão', 'Torneiras pingando', 'Ruído de "golpe de aríete"', 
            'Umidade em paredes (invisível)', 'Caixa d\'água suja', 'Corrosão metálica', 'Bóia com defeito'
        ],
        'Soluções': [
            'Substituição de conexões', 'Limpeza de crivos e filtros', 'Troca de vedantes (reparos)', 
            'Instalação de válvulas de alívio', 'Geofonamento e reparo pontual', 'Limpeza e desinfecção', 'Substituição por PVC/PEX'
        ]
    },
    'Esgotamento': {
        'Problemas': [
            'Retorno de mau cheiro', 'Entupimento de ramais', 'Caixa de gordura saturada', 'Rompimento de tubos de queda', 
            'Caixa de inspeção quebrada', 'Pragas (baratas/ratos)', 'Vazamento em anel de vedação de vaso'
        ],
        'Soluções': [
            'Revisão de ventilação secundária', 'Hidrojateamento', 'Limpeza total da caixa', 'Substituição de trecho', 
            'Recomposição da tampa', 'Dedetização e vedação', 'Substituição do anel de vedação'
        ]
    },
    'Drenagem': {
        'Problemas': [
            'Acúmulo de poças d\'água', 'Ralos obstruídos', 'Caixas de areia cheias', 'Canaletas com caimento negativo', 
            'Bocas de lobo quebradas', 'Erosão de taludes', 'Infiltração em muros de arrimo'
        ],
        'Soluções': [
            'Correção de caimento de piso', 'Desobstrução manual', 'Limpeza periódica', 'Recomposição de canaleta', 
            'Reparo em concreto/grades', 'Plantio de grama/contenção', 'Execução de barbacãs e drenos'
        ]
    },
    'Elétrica': {
        'Problemas': [
            'Fios expostos', 'Quadro sem identificação', 'Disjuntores desarmando', 'Aquecimento de condutores', 
            'Falta de aterramento', 'Luminárias piscando', 'Tomadas queimadas', 'Falta de DR'
        ],
        'Soluções': [
            'Acondicionamento em eletrodutos', 'Etiquetagem de circuitos', 'Redimensionamento de carga', 
            'Troca de condutores', 'Instalação de malha de terra', 'Troca de reator/lâmpada', 'Instalação de DR'
        ]
    }
}

lista_disciplinas = ["Escolha..."] + list(sugestoes.keys()) + ["Outras"]

# 4. BARRA LATERAL (SIDEBAR)
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>⚙️ PRODIN - IFBA</h1>", unsafe_allow_html=True)
    
    eng_sel = st.selectbox("Engenheiro Responsável", list(dados_prodin.keys()))
    
    # --- LOGICA DE AVATAR À PROVA DE ERROS ---
    genero = dados_prodin[eng_sel]["genero"]
    
    # Links novos e distintos para garantir a mudança visual
    if genero == "F":
        # Ícone de mulher engenheira
        url_img = "https://cdn-icons-png.flaticon.com/512/3135/3135768.png"
    else:
        # Ícone de homem engenheiro
        url_img = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        
    col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
    with col_img2:
        try:
            # O parâmetro '?v=' força o Streamlit a recarregar a imagem do servidor
            st.image(f"{url_img}?v={eng_sel.replace(' ', '')}", use_container_width=True)
        except:
            st.write("👤")

    campus_sel = st.selectbox("Campus", dados_prodin[eng_sel]["campi"])
    st.divider()
    choice = st.radio("Navegação", ["Nova Inspeção", "Histórico / PDF"])

# 5. FUNÇÃO PARA GERAR PDF
def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RELATÓRIO DE INSPEÇÃO PREDIAL - IFBA", ln=True, align='C')
    pdf.ln(10)
    for chave, valor in dados.items():
        if chave != "Foto_Dados":
            pdf.set_font("Arial", 'B', 11); pdf.cell(40, 8, f"{chave}:", 0)
            pdf.set_font("Arial", size=11); pdf.multi_cell(0, 8, f"{str(valor)}", 0); pdf.ln(2)
    if dados.get("Foto_Dados"):
        try:
            img_data = base64.b64decode(dados["Foto_Dados"])
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
            img.save("temp_report.jpg", "JPEG")
            pdf.ln(5); pdf.cell(200, 10, "EVIDÊNCIA FOTOGRÁFICA:", ln=True)
            pdf.image("temp_report.jpg", x=10, w=100)
        except: pass
    return pdf.output(dest='S').encode('latin-1', 'replace')

# 6. CONEXÃO
conn = st.connection("gsheets", type=GSheetsConnection)

if choice == "Nova Inspeção":
    st.header("📋 Registrar Inspeção Técnica")
    disciplina = st.selectbox("1. Escolha a Disciplina Técnica:", lista_disciplinas)
    
    with st.form("form_prodin_final", clear_on_submit=True):
        col_ed, col_dt = st.columns([2, 1])
        with col_ed:
            edificacao = st.selectbox("Edificação", ["Pavilhão de Aulas", "Pavilhão Administrativo", "Refeitório", "Ginásio", "Muro", "Estacionamento", "Guarita", "Galpão", "Usina Solar"])
        with col_dt:
            data_ins = st.date_input("Data da Inspeção", datetime.now())

        col_amb, col_num = st.columns([2, 1])
        with col_amb:
            ambiente = st.selectbox("Ambiente", ["Laboratório", "Sala Adm", "Sala de Aula", "Sanitário M", "Sanitário F", "Sanitário PCD", "Corredor", "Área Externa"])
        with col_num:
            sala_num = st.text_input("Nº Sala")

        ambiente_final = f"{ambiente} - {sala_num}" if sala_num else ambiente
        desc_final, sol_final = "", ""

        if disciplina in sugestoes:
            st.divider()
            pat_sel = st.selectbox("Patologia Identificada:", sugestoes[disciplina]['Problemas'])
            desc_final = st.text_area("Detalhamento:", value=pat_sel)
            sol_sel = st.selectbox("Solução Recomendada:", sugestoes[disciplina]['Soluções'])
            sol_final = st.text_area("Encaminhamento:", value=sol_sel)
        
        foto = st.file_uploader("📸 Foto da Evidência", type=['jpg', 'jpeg', 'png'])

        if st.form_submit_button("✅ Salvar na Planilha"):
            if disciplina == "Escolha...":
                st.error("Selecione a disciplina!")
            else:
                foto_b64 = ""
                if foto:
                    img = Image.open(foto); img.thumbnail((700, 700))
                    buf = io.BytesIO(); img.save(buf, format="JPEG", quality=70)
                    foto_b64 = base64.b64encode(buf.getvalue()).decode()

                novo_reg = pd.DataFrame([{
                    "Data": data_ins.strftime("%d/%m/%Y"), "Campus": campus_sel, "Edificacao": edificacao, 
                    "Disciplina": disciplina, "Ambiente": ambiente_final, "Descricao": desc_final, 
                    "Solucoes": sol_final, "Engenheiro": eng_sel, "Foto_Dados": foto_b64
                }])
                try:
                    df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
                    df_f = pd.concat([df, novo_reg], ignore_index=True)
                    conn.update(spreadsheet=URL_PLANILHA, data=df_f)
                    st.success("✅ Registro salvo!")
                except:
                    st.error("Erro ao salvar. Verifique o link da planilha.")

elif choice == "Histórico / PDF":
    st.header("📂 Histórico de Inspeções")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        st.dataframe(df.drop(columns=['Foto_Dados'], errors='ignore'), use_container_width=True)
        if not df.empty:
            id_sel = st.selectbox("Selecione o ID para PDF:", df.index)
            reg = df.iloc[id_sel]
            pdf_b = gerar_pdf(reg.to_dict())
            st.download_button("📥 Baixar PDF", data=pdf_b, file_name=f"Inspecao_{id_sel}.pdf", mime="application/pdf")
    except:
        st.error("Erro ao carregar banco de dados.")

# 7. RODAPÉ
st.markdown("<br><hr><div style='text-align: center; color: gray;'><strong>Desenvolvido por:</strong><br>Thiago Messias Carvalho Soares & Roger Ramos Santana<br>PRODIN - IFBA 2026</div>", unsafe_allow_html=True)
