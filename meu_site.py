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

# 🔗 COLOQUE O LINK DA SUA PLANILHA AQUI
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

# 3. BANCO DE DADOS TÉCNICO E MAPEAMENTO (SUPER AMPLIADO E CORRIGIDO)
mapa_engenheiros = {
    "Eng. Thiago": "M",
    "Eng. Roger": "M",
    "Eng. Laís": "F",
    "Eng. Larissa": "F",
    "Eng. Marcelo": "M",
    "Eng. Fenelon": "M"
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

# 4. BARRA LATERAL (SIDEBAR) COM LÓGICA DE GÊNERO CORRIGIDA
with st.sidebar:
    st.title("⚙️ PRODIN - IFBA")
    
    eng_sel = st.selectbox("Engenheiro Responsável", list(mapa_engenheiros.keys()))
    
    # --- LÓGICA DE AVATAR SEM CAPACETE CORRIGIDA ---
    genero = mapa_engenheiros[eng_sel]
    
    if genero == "M":
        # Ícone de Homem Profissional (sem capacete)
        icon_url = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    else:
        # Ícone de Mulher Profissional (sem capacete, corrigido)
        icon_url = "https://cdn-icons-png.flaticon.com/512/3135/3135768.png"
        
    try:
        # Baixa e exibe a imagem de forma estável
        response = requests.get(icon_url)
        img_avatar = Image.open(io.BytesIO(response.content))
        st.image(img_avatar, width=120)
    except:
        # Fallback caso o link quebre
        st.write("👨‍💼" if genero == "M" else "👩‍💼")
    # ------------------------------------------------------------------

    campus_sel = st.selectbox("Campus", ["Euclides da Cunha", "Feira de Santana", "Salvador", "Camaçari", "Vitória da Conquista", "Santo Amaro", "Simões Filho", "Eunápolis"])
    choice = st.sidebar.radio("Navegação", ["Nova Inspeção", "Histórico / PDF"])

# 5. CONEXÃO E FUNÇÕES
conn = st.connection("gsheets", type=GSheetsConnection)

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RELATÓRIO DE INSPEÇÃO PREDIAL - IFBA", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    for k, v in dados.items():
        if k != "Foto_Dados":
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(50, 7, f"{k}:", 0)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 7, f"{str(v)}", 0)
    return pdf.output(dest='S').encode('latin-1')

# --- TELA: NOVA INSPEÇÃO ---
if choice == "Nova Inspeção":
    st.header("📋 Registrar Inspeção Técnica")
    
    # Interatividade fora do form para carregar patologias automático
    disciplina = st.selectbox("1. Escolha a Disciplina Técnica:", lista_disciplinas)
    
    with st.form("form_vFinal_Super", clear_on_submit=True):
        col_ed, col_dt = st.columns([2, 1])
        with col_ed:
            edificacao = st.selectbox("Edificação / Bloco", ["Pavilhão de Aulas", "Pavilhão Administrativo", "Refeitório", "Ginásio", "Muro", "Estacionamento", "Guarita", "Galpão Industrial", "Usina de Biodiesel", "Usina Solar"])
        with col_dt:
            data_ins = st.date_input("Data da Inspeção", datetime.now())

        col_amb, col_num = st.columns([2, 1])
        with col_amb:
            ambiente = st.selectbox("Ambiente / Sala", ["Laboratório", "Sala Administrativa", "Sala de Aulas", "Sanitário Masculino", "Sanitário Feminino", "Sanitário PCD", "Corredor", "Área Externa", "Outro"])
        with col_num:
            sala_num = st.text_input("Nº Sala", placeholder="Ex: 102")

        ambiente_final = f"{ambiente} - {sala_num}" if sala_num else ambiente
        
        desc_final = ""
        sol_final = ""

        # Lógica de Botões Automáticos de Patologia
        if disciplina in sugestoes:
            st.markdown(f"---")
            st.info(f"Opções Técnicas para {disciplina}")
            pat_sel = st.selectbox("Patologia Identificada:", sugestoes[disciplina]['Problemas'])
            desc_final = st.text_area("Detalhamento da Patologia:", value=pat_sel)
            
            sol_sel = st.selectbox("Solução Recomendada:", sugestoes[disciplina]['Soluções'])
            sol_final = st.text_area("Sugestão de Encaminhamento:", value=sol_sel)
        
        elif disciplina == "Outras":
            desc_final = st.text_area("Descreva a Patologia:")
            sol_final = st.text_area("Descreva a Solução Sugerida:")

        foto = st.file_uploader("📸 Foto da Evidência", type=['jpg', 'jpeg', 'png'])

        if st.form_submit_button("✅ Salvar na Planilha"):
            if disciplina == "Escolha...":
                st.error("Por favor, selecione a disciplina acima!")
            else:
                foto_b64 = ""
                if foto:
                    img = Image.open(foto)
                    # Redimensiona mantendo a proporção para não estourar a planilha
                    img.thumbnail((700, 700)) 
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=70)
                    foto_b64 = base64.b64encode(buf.getvalue()).decode()

                novo_reg = pd.DataFrame([{
                    "Data": data_ins.strftime("%d/%m/%Y"), 
                    "Campus": campus_sel, 
                    "Edificacao": edificacao, 
                    "Disciplina": disciplina, 
                    "Ambiente": ambiente_final,
                    "Descricao": desc_final, 
                    "Solucoes": sol_final, 
                    "Engenheiro": eng_sel, 
                    "Foto_Dados": foto_b64
                }])

                try:
                    df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
                    df_f = pd.concat([df, novo_reg], ignore_index=True)
                    conn.update(spreadsheet=URL_PLANILHA, data=df_f)
                    st.success("✅ Registro salvo com sucesso na planilha!")
                except Exception as e:
                    st.error(f"Erro ao conectar com a planilha: {e}")

# --- TELA: HISTÓRICO ---
elif choice == "Histórico / Gerar PDF":
    st.header("📂 Histórico de Inspeções")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        # Exibe a tabela sem a coluna gigante de texto da foto
        st.dataframe(df.drop(columns=['Foto_Dados'], errors='ignore'), use_container_width=True)
        
        if not df.empty:
            st.divider()
            id_sel = st.selectbox("Selecione o ID para ver detalhes:", df.index)
            reg = df.iloc[id_sel]
            
            c1, c2 = st.columns([1, 1])
            with c1:
                if reg["Foto_Dados"]:
                    st.image(base64.b64decode(reg["Foto_Dados"]), caption="Evidência", use_container_width=True)
            with c2:
                st.write(f"**Engenheiro:** {reg['Engenheiro']}")
                st.write(f"**Data:** {reg['Data']}")
                st.write(f"**Descrição:** {reg['Descricao']}")
                
                # Gerador de PDF
                pdf_bytes = gerar_pdf(reg.to_dict())
                st.download_button(label="📥 Baixar PDF", data=pdf_bytes, 
                                 file_name=f"Inspecao_{reg['Campus']}_{id_sel}.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"Não foi possível carregar o banco de dados: {e}")

# --- RODAPÉ CENTRALIZADO NA PÁGINA ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #6d6d6d; font-size: 1.1em; line-height: 1.5;">
        <strong>Desenvolvido por:</strong><br>
        Thiago Messias Carvalho Soares & Roger Ramos Santana<br>
        <strong style="color: #2e7d32;">PRODIN - IFBA 2026</strong>
    </div>
    """,
    unsafe_allow_html=True
)
