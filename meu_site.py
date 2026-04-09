import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from datetime import datetime
from PIL import Image

# 1. Sistema de Autenticação (Senha: IFBA2026)
def verificar_senha():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if not st.session_state["autenticado"]:
        st.set_page_config(page_title="Login - Inspeção IFBA", page_icon="🔐")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔐 Acesso Restrito")
            st.subheader("Sistema de Inspeção IFBA")
            senha = st.text_input("Digite a senha de acesso:", type="password")
            if st.button("Entrar"):
                if senha == "IFBA2026":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
        return False
    return True

if verificar_senha():
    st.set_page_config(page_title="Inspeção Predial IFBA", layout="wide", page_icon="🏗️")

    # --- CABEÇALHO LIMPO ---
    url_construcao = "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?q=80&w=300&auto=format&fit=crop"
    
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; background-color: #fcfcfc; padding: 25px; border-radius: 20px; border-left: 12px solid #2e7d32; border-bottom: 2px solid #e0e0e0; margin-bottom: 30px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
            <div style="margin-right: 25px;">
                <img src="{url_construcao}" style="width: 180px; height: 120px; border-radius: 12px; object-fit: cover; border: 1px solid #ddd;">
            </div>
            <div style="flex-grow: 1;">
                <h1 style="margin: 0; color: #1e4620; font-family: sans-serif; font-size: 38px;">Sistema de Inspeção Predial - IFBA</h1>
                <p style="margin: 0; color: #666; font-size: 18px; font-weight: 300;">Engenharia, Manutenção e Vistorias Técnicas</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df_base = conn.read(ttl="0")
        df_base = df_base.reset_index(drop=True)
    except:
        df_base = pd.DataFrame()

    # --- SIDEBAR COM TODOS OS CAMPI DO IFBA ---
    with st.sidebar:
        st.header("🏢 Unidades IFBA")
        
        # Lista completa de Campi e Núcleos Avançados
        lista_campi = sorted([
            "Salvador", "Feira de Santana", "Barreiras", "Brumado", "Camaçari", 
            "Euclides da Cunha", "Eunápolis", "Ilhéus", "Irecê", "Jacobina", 
            "Jequié", "Juazeiro", "Paulo Afonso", "Porto Seguro", "Santo Amaro", 
            "Santo Antônio de Jesus", "Seabra", "Simões Filho", "Valença", 
            "Vitória da Conquista", "Ubaitaba", "Jaguarari", "Salinas da Margarida"
        ])
        
        campus_sel = st.selectbox("Selecione o Campus para trabalhar:", lista_campi)
        
        st.markdown("---")
        st.subheader("🛠️ Modo de Edição")
        df_campus = df_base[df_base['Campus'] == campus_sel] if not df_base.empty else pd.DataFrame()
        
        edit_mode = False
        index_to_edit = None
        dados_edit = None
        
        if not df_campus.empty:
            opcoes_edit = ["Nova Inspeção"] + [f"ID {i} - {row['Edificacao']}" for i, row in df_campus.iterrows()]
            selecao = st.selectbox("Selecione para editar:", opcoes_edit)
            
            if selecao != "Nova Inspeção":
                edit_mode = True
                index_to_edit = int(selecao.split(" ")[1])
                dados_edit = df_base.iloc[index_to_edit]

        if st.button("🚪 Sair do Sistema"):
            st.session_state["autenticado"] = False
            st.rerun()

    # Formulário de Vistoria
    with st.form("form_vistoria", clear_on_submit=not edit_mode):
        titulo_form = f"✏️ Editando: {dados_edit['Edificacao']}" if edit_mode else f"📝 Nova Vistoria: {campus_sel}"
        st.subheader(titulo_form)
        
        c1, c2 = st.columns(2)
        with c1:
            edificacao = st.text_input("Edificação/Bloco:", value=dados_edit['Edificacao'] if edit_mode else "", key="edif")
            disciplina_lista = ["Alvenaria", "Estrutura", "Elétrica", "Hidráulica", "Pintura", "Cobertura", "Drenagem", "Incêndio"]
            idx_disc = disciplina_lista.index(dados_edit['Disciplina']) if edit_mode and dados_edit['Disciplina'] in disciplina_lista else 0
            disciplina = st.selectbox("Disciplina:", disciplina_lista, index=idx_disc)
            
            ambiente = st.text_input("Ambiente/Local:", value=dados_edit['Ambiente'] if edit_mode else "")
            descricao = st.text_area("Descrição da Patologia:", value=dados_edit['Descricao'] if edit_mode else "")
            solucoes = st.text_area("Soluções Sugeridas:", value=dados_edit['Solucoes'] if edit_mode else "")
            
        with c2:
            st.write("**📸 Evidência Fotográfica**")
            foto_upload = st.file_uploader("Arraste a foto", type=["jpg", "png", "jpeg"])
            if foto_upload:
                st.image(Image.open(foto_upload), caption="Visualização Técnica", use_container_width=True)
            elif edit_mode and dados_edit['Foto'] != "Sem foto":
                st.info(f"O registro possui foto anexada ({dados_edit['Foto']}).")

            st.write("**Avaliação GUT**")
            g = st.slider("Gravidade", 1, 5, 3)
            u = st.slider("Urgência", 1, 5, 3)
            t = st.slider("Tendência", 1, 5, 3)
            score = g * u * t
            status = "CRÍTICA" if score > 60 else "MÉDIA" if score > 20 else "BAIXA"
            st.metric("Prioridade", status, f"Score: {score}")

        btn_label = "💾 Atualizar Registro" if edit_mode else "💾 Salvar Nova Inspeção"
        if st.form_submit_button(btn_label):
            nova_linha = {
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Campus": campus_sel,
                "Edificacao": edificacao,
                "Disciplina": disciplina,
                "Ambiente": ambiente,
                "Descricao": descricao,
                "Solucoes": solucoes,
                "Foto": "Anexada" if foto_upload else (dados_edit['Foto'] if edit_mode else "Sem foto"),
                "Score_GUT": score,
                "Status": status
            }
            if edit_mode:
                df_base.iloc[index_to_edit] = nova_linha
            else:
                df_base = pd.concat([df_base, pd.DataFrame([nova_linha])], ignore_index=True)
            conn.update(data=df_base)
            st.success("Inspeção registrada com sucesso!")
            st.rerun()

    # Dashboards e Histórico
    if not df_base.empty:
        df_filtrado = df_base[df_base['Campus'] == campus_sel]
        if not df_filtrado.empty:
            st.markdown("---")
            st.subheader(f"📊 Análise de Prioridades GUT - {campus_sel}")
            
            edif_para_grafico = st.selectbox("Filtrar gráfico por edificação:", ["Todas"] + sorted(df_filtrado['Edificacao'].unique().tolist()))
            df_grafico = df_filtrado if edif_para_grafico == "Todas" else df_filtrado[df_filtrado['Edificacao'] == edif_para_grafico]
            
            fig = px.pie(
                df_grafico, 
                names='Status', 
                title=f"Distribuição GUT: {edif_para_grafico}",
                color='Status',
                color_discrete_map={'CRÍTICA': '#d32f2f', 'MÉDIA': '#fbc02d', 'BAIXA': '#388e3c'}
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.subheader(f"📋 Histórico de Inspeções - {campus_sel}")
            st.dataframe(df_filtrado.drop(columns=["Campus"]), use_container_width=True)

    # --- RODAPÉ ---
    st.markdown("---")
    st.markdown(
        """
        <div style="background-color: #f1f3f6; padding: 25px; border-radius: 15px; text-align: center; border-top: 1px solid #ddd; margin-top: 30px; box-shadow: 1px 1px 3px rgba(0,0,0,0.05);">
            <p style="margin: 0; color: #1e4620; font-family: sans-serif; font-size: 18px; font-weight: bold; border-bottom: 1px solid #c8e6c9; padding-bottom: 5px;">Inspeção Predial IFBA</p>
            <p style="margin: 0; color: #666; font-size: 14px; padding-top: 10px;">🚀 Engenharia e Manutenção</p>
            <p style="margin: 10px 0 0 0; color: #555; font-size: 13px; font-style: italic;">Desenvolvido por <b>Thiago Messias Carvalho Soares</b></p>
        </div>
        """,
        unsafe_allow_html=True
    )
