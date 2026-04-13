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

# 3. BANCO DE DADOS TÉCNICO (TODAS AS PATOLOGIAS CORRIGIDAS)
# Mapeamento de Engenheiros e Gênero (M: Masculino, F: Feminino) para o Avatar
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
        'Problemas': ['Fissuras de retração térmica', 'Trincas em diagonal', 'Umidade ascendente', 'Eflorescência', 'Desaprumo', 'Fissuras em H (esmagamento)', 'Mofo/bolor'],
        'Soluções': ['Tela de poliéster e selante', 'Grampeamento com barras de aço', 'Impermeabilização polimérica', 'Limpeza química', 'Regularização de prumo']
    },
    'Estrutura': {
        'Problemas': ['Corrosão de armaduras', 'Ferragem exposta', 'Bicheiras (segregação)', 'Flechas excessivas', 'Carbonatação do concreto'],
        'Soluções': ['Passivação e recomposição', 'Tratamento anticorrosivo', 'Grauteamento estrutural', 'Reforço com fibra de carbono', 'Injeção de epóxi']
    },
    'Pavimentação': {
        'Problemas': ['Peças soltas', 'Buracos/Panelas', 'Desnível por recalque', 'Trincas couro de jacaré', 'Meio-fio quebrado'],
        'Soluções': ['Recomposição de base', 'Tapa-buraco asfáltico', 'Compactação e correção de cota', 'Alinhamento de guias']
    },
    'Cobertura': {
        'Problemas': ['Telhas quebradas', 'Calhas obstruídas', 'Infiltração em rufos', 'Oxidação estrutural', 'Goteiras'],
        'Soluções': ['Substituição de peças', 'Limpeza manual', 'Vedação com PU 40', 'Pintura anticorrosiva']
    },
    'Revestimento': {
        'Problemas': ['Descolamento cerâmico (som cavo)', 'Eflorescência em rejuntes', 'Descascamento de pintura', 'Reboco esfarelando'],
        'Soluções': ['Novo assentamento AC-III', 'Limpeza ácida e rejunte impermeável', 'Raspagem e nova pintura', 'Remoção e novo reboco']
    },
    'Esquadrias': {
        'Problemas': ['Dificuldade de deslize', 'Oxidação metálica', 'Vidros soltos', 'Falta de vedação', 'Braços travados', 'Fechadura com defeito'],
        'Soluções': ['Limpeza de trilhos e roldanas', 'Tratamento de corrosão e pintura esmalte', 'Substituição e silicone', 'Novas guarnições', 'Lubrificação de ferragens']
    },
    'Hidráulica': {
        'Problemas': ['Vazamento aparente', 'Baixa pressão nos pontos', 'Registros pingando', 'Golpe de aríete', 'Umidade invisível (parede)'],
        'Soluções': ['Substituição de conexões', 'Limpeza de filtros', 'Troca de vedantes (reparos)', 'Instalação de válvula de alívio']
    },
    'Esgotamento': {
        'Problemas': ['Mau cheiro (sifonagem)', 'Entupimento de ramais', 'Caixa de gordura saturada', 'Vazamento em vaso (anel)'],
        'Soluções': ['Revisão de ventilação secundária', 'Hidrojateamento', 'Limpeza total da caixa', 'Substituição do anel de vedação']
    },
    'Drenagem': {
        'Problemas': ['Acúmulo de poças d\'água', 'Ralos obstruídos', 'Caixas de areia cheias', 'Caimento negativo'],
        'Soluções': ['Correção de caimento de piso', 'Desobstrução manual', 'Limpeza periódica', 'Recomposição de canaleta']
    },
    'Elétrica': {
        'Problemas': ['Fios expostos', 'Quadro sem identificação', 'Disjuntores desarmando', 'Aquecimento (Efeito Joule)', 'Falta de DR', 'Aterramento inexistente'],
        'Soluções': ['Isolamento em eletrodutos', 'Etiquetagem de circuitos', 'Redimensionamento de carga', 'Instalação de DR', 'Instalação de malha de terra']
    }
}

lista_disciplinas = ["Escolha..."] + list(sugestoes.keys()) + ["Outras"]

# 4. BARRA LATERAL (SIDEBAR) COM AVATARES DINÂMICOS
with st.sidebar:
    st.title("⚙️ PRODIN - IFBA")
    
    # Seleção do Engenheiro (precisa vir antes para definir o avatar)
    eng_sel = st.selectbox("Engenheiro Responsável", list(mapa_engenheiros.keys()))
    
    # --- NOVIDADE SUPER: AVATAR BONECO/BONECA COM CAPACETE BRANCO ---
    genero = mapa_engenheiros[eng_sel]
    
    if genero == "M":
        # Link do Boneco com Capacete Branco
        icon_url = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    else:
        # Link da Boneca com Capacete Branco
        icon_url = "https://cdn-icons-png.flaticon.com/512/1906/1906730.png"
        
    try:
        # Baixa e exibe a imagem de forma estável
        response = requests.get(icon_url)
        img_cap = Image.open(io.BytesIO(response.content))
        st.image(img_cap, width=120)
    except:
        # Fallback caso o link quebre
        st.write("👷🏗️" if genero == "M" else "👷‍♀️🏗️")
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
                st.write(f"**Solução:** {reg['Solucoes']}")
                
                # Gerador de PDF
                pdf_bytes = gerar_pdf(reg.to_dict())
                st.download_button(label="📥 Baixar Relatório PDF", data=pdf_bytes, 
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
