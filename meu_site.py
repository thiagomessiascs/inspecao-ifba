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

# 🔗 LINK DA SUA PLANILHA
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

# 3. BANCO DE DADOS TÉCNICO AMPLIADO
sugestoes = {
    "Alvenaria": {
        "Problemas": [
            "Fissuras de retração térmica", "Trincas em diagonal (esforço estrutural)", "Umidade por capilaridade (rodapé)", 
            "Eflorescência (sais brancos)", "Desaprumo evidente", "Descolamento de argamassa de assentamento", 
            "Fissuras em "H" (esmagamento)", "Presença de mofo/bolor", "Furos/Aberturas sem vedação"
        ],
        "Soluções": [
            "Tratamento com tela de poliéster e selante", "Grampeamento com barras de aço e graute", "Impermeabilização com argamassa polimérica", 
            "Limpeza química e hidrofugação", "Regularização de prumo e reforço", "Refazer junta de assentamento", 
            "Reforço de vergas e contravergas", "Tratamento biocida e pintura impermeável", "Vedação com espuma expansiva ou argamassa"
        ]
    },
    "Estrutura": {
        "Problemas": [
            "Corrosão de armaduras com expansão", "Exposição de ferragem oxidada", "Segregação do concreto (bicheiras)", 
            "Flechas excessivas (deformação)", "Fissuras de cisalhamento em vigas", "Desagregação do concreto por ataque químico",
            "Ninhos de concretagem", "Trincas em pilares", "Esmagamento de apoio"
        ],
        "Soluções": [
            "Escovamento, passivação e recomposição estrutural", "Tratamento anticorrosivo e grauteamento", "Limpeza e preenchimento com graute fluido", 
            "Escoramento e reforço com fibra de carbono ou chapas", "Injeção de resina de epóxi", "Remoção de concreto degradado e novo lançamento", 
            "Reparo localizado com argamassa tixotrópica", "Cálculo de reforço e jaquetamento", "Substituição de aparelhos de apoio"
        ]
    },
    "Pavimentação": {
        "Problemas": [
            "Peças de intertravado soltas ou quebradas", "Buracos/Panelas (potholes)", "Desnível por recalque de base", 
            "Trincas couro de jacaré (fadiga)", "Exsudação de ligante", "Meio-fio deslocado ou quebrado",
            "Acúmulo de lama/areia", "Falta de rejuntamento", "Afundamento de trilha de roda"
        ],
        "Soluções": [
            "Recomposição de colchão de areia e travamento", "Tapa-buraco com massa asfáltica a frio/quente", "Compactação de base e correção de cota", 
            "Fresagem e recapeamento", "Aplicação de agregados/selagem", "Alinhamento e reassentamento de guias", 
            "Limpeza e varredura", "Aplicação de areia/pedrisco de selagem", "Correção de sub-base e nova camada de rolamento"
        ]
    },
    "Cobertura": {
        "Problemas": [
            "Telhas quebradas ou fissuradas", "Telhas deslocadas (ação do vento)", "Calhas obstruídas por detritos", 
            "Corrosão em calhas metálicas", "Infiltração em rufos e águas-furtadas", "Estrutura metálica com oxidação",
            "Estrutura de madeira com cupim/podridão", "Pontos de goteira", "Falta de vedação em parafusos"
        ],
        "Soluções": [
            "Substituição imediata das peças avariadas", "Revisão de fixação e amarração", "Limpeza e desobstrução manual", 
            "Pintura betuminosa ou substituição de trecho", "Substituição de rufos e selagem com PU 40", "Lixamento e pintura anticorrosiva", 
            "Imunização química ou troca de peças", "Identificação e vedação localizada", "Troca de parafusos com arruelas de vedação"
        ]
    },
    "Revestimento": {
        "Problemas": [
            "Descolamento cerâmico (som cavo)", "Eflorescência em rejuntes", "Descascamento/Bolhas na pintura", 
            "Reboco esfarelando (fraco)", "Fissuras mapeadas (tipo teia de aranha)", "Cerâmica trincada",
            "Mofo excessivo em áreas úmidas", "Perda de brilho/Desgaste", "Juntas de dilatação obstruídas"
        ],
        "Soluções": [
            "Remoção e novo assentamento com argamassa AC-III", "Limpeza ácida e novo rejuntamento impermeável", "Raspagem, fundo preparador e repintura", 
            "Remoção total e novo reboco com aditivo", "Aplicação de selador e massa corrida/acrílica", "Troca da peça cerâmica", 
            "Limpeza com cloro e ventilação", "Polimento ou aplicação de resina", "Limpeza de juntas e preenchimento com selante elástico"
        ]
    },
    "Esquadrias": {
        "Problemas": [
            "Dificuldade de deslize (trilhos)", "Oxidação em marcos metálicos", "Vidros quebrados ou soltos", 
            "Falta de vedação (borrachas/escovas)", "Braços de articulação travados", "Fechaduras/Maçanetas com defeito",
            "Infiltração pela guarnição", "Ruído excessivo ao bater", "Desaprumo de portas"
        ],
        "Soluções": [
            "Limpeza de trilhos e lubrificação de roldanas", "Tratamento de corrosão e pintura esmalte", "Troca de vidros e nova vedação com silicone", 
            "Instalação de novas guarnições", "Substituição de ferragens e lubrificação", "Troca do miolo ou lubrificação", 
            "Vedação externa com selante PU", "Instalação de batedores/amortecedores", "Ajuste de dobradiças e prumo"
        ]
    },
    "Hidráulica": {
        "Problemas": [
            "Vazamento aparente em conexões", "Baixa pressão nos pontos terminais", "Torneiras/Registros com gotejamento", 
            "Ruído de 'golpe de aríete'", "Umidade em paredes (vazamento invisível)", "Caixa d'água suja ou sem tampa",
            "Corrosão em tubulações metálicas", "Filtros obstruídos", "Bóia da caixa com defeito"
        ],
        "Soluções": [
            "Substituição de conexões/trechos de tubulação", "Limpeza de crivos e verificação de pressão", "Troca de reparos e vedantes", 
            "Instalação de válvulas de alívio", "Geofonamento e reparo pontual", "Limpeza, desinfecção e fechamento", 
            "Substituição por PVC/PEX", "Limpeza manual dos elementos filtrantes", "Troca do conjunto da bóia"
        ]
    },
    "Esgotamento": {
        "Problemas": [
            "Retorno de mau cheiro (sifonagem)", "Entupimento de ramais", "Caixa de gordura saturada", 
            "Rompimento de tubos de queda", "Caixa de inspeção quebrada", "Presença de pragas (baratas/ratos)",
            "Vazamento em vaso sanitário (anel de vedação)", "Falta de ventilação secundária", "Raízes de árvores na rede"
        ],
        "Soluções": [
            "Verificação de fecho hídrico e coluna de ventilação", "Hidrojateamento ou limpeza mecânica", "Limpeza total e descarte adequado", 
            "Substituição de trecho avariado", "Recomposição de alvenaria/tampa da caixa", "Dedetização e vedação de frestas", 
            "Substituição do anel de vedação", "Execução de terminal de ventilação", "Limpeza de rede e remoção de raízes"
        ]
    },
    "Drenagem": {
        "Problemas": [
            "Acúmulo de água (poças)", "Ralos de águas pluviais entupidos", "Caixas de areia obstruídas", 
            "Canaletas com caimento negativo", "Bocas de lobo quebradas", "Erosão de taludes adjacentes",
            "Infiltração em muros de arrimo", "Falta de dreno de pé", "Drenos de parede obstruídos"
        ],
        "Soluções": [
            "Correção de caimento de piso/pavimento", "Desobstrução manual e jateamento", "Limpeza periódica de sedimentos", 
            "Recomposição de fundo de canaleta", "Reparo em concreto/grade metálica", "Plantio de grama ou contenção", 
            "Execução de barbacãs e drenagem", "Instalação de tubo dreno perfurado", "Limpeza e desobstrução de barbacãs"
        ]
    },
    "Elétrica": {
        "Problemas": [
            "Fios expostos ou emendas sem isolamento", "Quadro de energia sem identificação/esquema", "Disjuntores desarmando (sobrecarga)", 
            "Aquecimento de fiação (efeito Joule)", "Falta de aterramento", "Luminárias inoperantes ou piscando",
            "Tomadas com mau contato/queimadas", "Barramentos oxidados", "Falta de DR (dispositivo residual)"
        ],
        "Soluções": [
            "Acondicionamento em eletrodutos e fita isolante", "Identificação de circuitos e etiquetagem", "Redimensionamento de carga ou troca de disjuntor", 
            "Troca de condutores por bitola adequada", "Instalação de haste e malha de aterramento", "Troca de reator/lâmpada/starter", 
            "Substituição de módulos de tomada", "Limpeza química e reaperto", "Instalação de proteção contra choque (DR)"
        ]
    }
}

lista_disciplinas = ["Escolha..."] + list(sugestoes.keys()) + ["Outras"]

# 4. SIDEBAR E INFOS
st.sidebar.title("⚙️ PRODIN - IFBA")
eng_sel = st.sidebar.selectbox("Engenheiro Responsável", ["Eng. Thiago", "Eng. Roger", "Eng. Laís", "Eng. Larissa", "Eng. Marcelo", "Eng. Fenelon"])
campus_sel = st.sidebar.selectbox("Campus", ["Salvador", "Feira de Santana", "Camaçari", "Vitória da Conquista", "Santo Amaro", "Simões Filho", "Eunápolis"])
choice = st.sidebar.radio("Navegação", ["Nova Inspeção", "Histórico / Gerar PDF"])

# 5. CONEXÃO E PDF
conn = st.connection("gsheets", type=GSheetsConnection)

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RELATÓRIO DE INSPEÇÃO PREDIAL - IFBA", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    for k, v in dados.items():
        if k != "Foto_Dados":
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(50, 7, f"{k}:", 0)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 7, f"{str(v)}", 0)
            pdf.ln(1)
    return pdf.output(dest='S').encode('latin-1')

# --- TELA: NOVA INSPEÇÃO ---
if choice == "Nova Inspeção":
    st.header("📋 Registro de Inspeção Técnica")
    
    # Campo fora do form para interatividade imediata
    disciplina = st.selectbox("1. Escolha a Disciplina:", lista_disciplinas)
    
    with st.form("form_prodin_v3", clear_on_submit=True):
        col_ed, col_dt = st.columns([2, 1])
        with col_ed:
            edificacao = st.selectbox("Edificação / Bloco", [
                "Pavilhão de Aulas", "Pavilhão Administrativo", "Refeitório", "Ginásio", 
                "Muro", "Estacionamento", "Guarita", "Galpão Industrial", "Usina de Biodiesel", "Usina Solar"
            ])
        with col_dt:
            data_ins = st.date_input("Data", datetime.now())

        col_amb, col_num = st.columns([2, 1])
        with col_amb:
            ambiente = st.selectbox("Ambiente / Sala", ["Laboratório", "Sala Administrativa", "Sala de Aulas", "Sanitário Masculino", "Sanitário Feminino", "Sanitário PCD", "Corredor", "Área Externa"])
        with col_num:
            sala_num = st.text_input("Nº da Sala", placeholder="Ex: 102")

        ambiente_final = f"{ambiente} - {sala_num}" if sala_num else ambiente
        
        descricao = ""
        solucoes_txt = ""

        if disciplina in sugestoes:
            st.divider()
            st.markdown(f"**🔍 Sugestões Técnicas para {disciplina}:**")
            pat_sel = st.selectbox("Patologia mais provável:", sugestoes[disciplina]["Problemas"])
            descricao = st.text_area("Detalhamento da Patologia:", value=pat_sel)
            
            sol_sel = st.selectbox("Solução sugerida:", sugestoes[disciplina]["Soluções"])
            solucoes_txt = st.text_area("Encaminhamento / Solução:", value=sol_sel)
        
        elif disciplina == "Outras":
            descricao = st.text_area("Descreva a Patologia:")
            solucoes_txt = st.text_area("Descreva a Solução:")

        foto = st.file_uploader("📸 Anexar Foto (Evidência)", type=['jpg', 'jpeg', 'png'])

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
                    "Data": data_ins.strftime("%d/%m/%Y"), 
                    "Campus": campus_sel, 
                    "Edificacao": edificacao, 
                    "Disciplina": disciplina, 
                    "Ambiente": ambiente_final,
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
                    st.error(f"Erro ao salvar: {e}")

# --- TELA: HISTÓRICO ---
elif choice == "Histórico / Gerar PDF":
    st.header("📂 Histórico de Inspeções")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        st.dataframe(df.drop(columns=['Foto_Dados'], errors='ignore'), use_container_width=True)
        
        if not df.empty:
            id_sel = st.selectbox("Selecione para ver detalhes:", df.index)
            reg = df.iloc[id_sel]
            
            c1, c2 = st.columns([1, 1])
            with c1:
                if reg["Foto_Dados"]:
                    st.image(base64.b64decode(reg["Foto_Dados"]), caption="Evidência Fotográfica")
            with c2:
                st.write(f"**Engenheiro:** {reg['Engenheiro']}")
                st.write(f"**Data:** {reg['Data']}")
                
                pdf_bytes = gerar_pdf(reg.to_dict())
                st.download_button("📥 Baixar PDF deste Registro", data=pdf_bytes, file_name=f"Inspecao_{id_sel}.pdf")
    except:
        st.error("Banco de dados não disponível.")

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
