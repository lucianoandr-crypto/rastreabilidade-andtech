import streamlit as st
import database
import datetime

# 1. CONFIGURAÇÃO DA PÁGINA WEB (Sempre a primeira linha do script)
st.set_page_config(page_title="ANDTECH - Portal de Rastreabilidade", page_icon="⚙️", layout="wide")

# Conexão centralizada com a nuvem do Neon
conn = database.conectar_banco()

# 2. GERENCIAMENTO DE SESSÃO E LOGIN (Substitui a CentralLoginANDTECH do Tkinter)
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.modulo = ""

def realizar_logout():
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.modulo = ""
    st.rerun()

# TELA DE AUTENTICAÇÃO
if not st.session_state.logado:
    st.markdown("<h2 style='text-align: center;'>🔒 AUTENTICAÇÃO DE USUÁRIO — ANDTECH</h2>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        with st.form("form_login", clear_on_submit=True):
            user_input = st.text_input("Usuário / Login:")
            pass_input = st.text_input("Senha do Módulo:", type="*")
            botao_acessar = st.form_submit_button("ACESSAR SISTEMA", use_container_width=True)
            
            if botao_acessar:
                if not user_input or not pass_input:
                    st.error("Por favor, preencha o login e a senha!")
                else:
                    c = conn.cursor()
                    try:
                        c.execute("SELECT nome, modulo FROM usuarios WHERE login = %s AND senha = %s", (user_input.strip(), pass_input.strip()))
                        usuario_validado = c.fetchone()
                        
                        if usuario_validado:
                            st.session_state.logado = True
                            st.session_state.usuario = usuario_validado[0]
                            st.session_state.modulo = usuario_validado[1]
                            st.success(f"Bem-vindo, {usuario_validado[0]}!")
                            st.rerun()
                        else:
                            st.error("Usuário ou Senha incorretos!")
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Falha ao consultar credenciais: {e}")
    st.stop()

# --- SE O USUÁRIO PASSOU DO LOGIN, CONTINUA O CÓDIGO ABAIXO ---
# BARRA SUPERIOR DE STATUS E LOGOUT
col_s1, col_s2 = st.columns([4, 1])
with col_s1:
    st.markdown(f"👤 **Operador:** {st.session_state.usuario} | 🛡️ **Nível:** `{st.session_state.modulo}`")
with col_s2:
    st.button("🚪 Sair do Sistema", on_click=realizar_logout, use_container_width=True)

st.title("⚙️ Sistema Master de Rastreabilidade")
st.write(f"Conectado ao servidor Neon na Nuvem | {datetime.date.today().strftime('%d/%m/%Y')}")
st.divider()

# CONFIGURAÇÃO DE ABAS BASEADA NAS PERMISSÕES DO OPERADOR
mod = st.session_state.modulo
abas_disponiveis = []

if mod == "ADMINISTRADOR":
    abas_disponiveis = ["📋 PCP", "🏭 Produção", "🔬 CQ Qualidade", "🚚 Expedição", "🔑 Configurações ADM"]
elif mod == "PRODUCAO":
    abas_disponiveis = ["🏭 Produção"]
elif mod == "QUALIDADE":
    abas_disponiveis = ["🔬 CQ Qualidade"]
elif mod == "EXPEDICAO" or mod == "FATURAMENTO":
    abas_disponiveis = ["🚚 Expedição"]
else:
    abas_disponiveis = ["🏭 Produção"]

# Renderiza apenas as abas que o usuário tem direito de acessar
abas_sistema = st.tabs(abas_disponiveis)
# Mapeamento dinâmico para renderizar o conteúdo certo na aba certa
for idx, nome_aba in enumerate(abas_disponiveis):
    with abas_sistema[idx]:
        
        # --- MÓDULO 1: PCP (CADASTROS) ---
        if "PCP" in nome_aba:
            st.subheader("📋 Cadastro Inicial de Modelos e Ordens de Fabricação (OF)")
            col_pcp1, col_pcp2 = st.columns(2)
            
            with col_pcp1:
                st.markdown("#### Criar Novo Modelo de Produto")
                with st.form("cad_modelo_web", clear_on_submit=True):
                    nome_mod = st.text_input("Nome do Modelo (Ex: Placa Controladora X):")
                    ini_mod = st.text_input("Iniciais do Modelo (Ex: PCX):")
                    btn_mod = st.form_submit_button("Gravar Modelo no Neon", use_container_width=True)
                    
                    if btn_mod and nome_mod and ini_mod:
                        c = conn.cursor()
                        try:
                            c.execute("INSERT INTO modelos (nome, iniciais) VALUES (%s, %s)", (nome_mod.strip().upper(), ini_mod.strip().upper()))
                            conn.commit()
                            st.success("🎉 Modelo gravado com sucesso na nuvem!")
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Erro ao salvar modelo: {e}")

            with col_pcp2:
                st.markdown("#### Lançar Ordem de Fabricação / Serial")
                
                # Busca os modelos cadastrados para preencher o menu
                lista_modelos = {}
                c = conn.cursor()
                c.execute("SELECT id, nome, iniciais FROM modelos ORDER BY nome ASC")
                for m in c.fetchall():
                    lista_modelos[f"{m[1]} ({m[2]})"] = m[0]
                
                if lista_modelos:
                    with st.form("cad_serial_web", clear_on_submit=True):
                        mod_selecionado = st.selectbox("Selecione o Modelo:", list(lista_modelos.keys()))
                        of_num = st.text_input("Número da Ordem de Fabricação (OF):")
                        serial_manual = st.text_input("Número Serial (Bipado ou Digitado):")
                        btn_prod = st.form_submit_button("Enviar para a Fila da Fábrica", use_container_width=True)
                        
                        if btn_prod and of_num and serial_manual:
                            c = conn.cursor()
                            try:
                                id_mod = lista_modelos[mod_selecionado]
                                dt_hj = datetime.date.today().strftime("%d/%m/%Y")
                                c.execute("""
                                    INSERT INTO produtos (serial, numero_of, modelo_id, data_fabricacao, quem_validou) 
                                    VALUES (%s, %s, %s, %s, 'PENDENTE')
                                """, (serial_manual.strip().upper(), of_num.strip().upper(), id_mod, dt_hj))
                                conn.commit()
                                st.success(f"🚀 Serial {serial_manual.upper()} lançado para a produção!")
                            except Exception as e:
                                conn.rollback()
                                st.error(f"Erro ao lançar serial: {e}")
                else:
                    st.info("Cadastre ao menos um modelo primeiro para liberar o lançamento de seriais.")

        # --- MÓDULO 2: PRODUÇÃO (CHÃO DE FÁBRICA) ---
        elif "Produção" in nome_aba:
            st.subheader("🏭 Fila de Produção e Inserção de Lotes")
            
            c = conn.cursor()
            c.execute("""
                SELECT p.id, p.serial, p.numero_of, m.nome 
                FROM produtos p 
                JOIN modelos m ON p.modelo_id = m.id 
                WHERE p.quem_testou IS NULL OR p.quem_testou = ''
                ORDER BY p.id ASC
            """)
            fila_fabrica = c.fetchall()
            
            if fila_fabrica:
                seriais_fila = [f"{r[1]} | OF: {r[2]} ({r[3]})" for r in fila_fabrica]
                dict_fila = {f"{r[1]} | OF: {r[2]} ({r[3]})": r[0] for r in fila_fabrica}
                
                with st.form("form_producao_web", clear_on_submit=True):
                    serial_sel = st.selectbox("Escolha o Equipamento para Apontar:", seriais_fila)
                    lote_digitado = st.text_input("Lote de Placas Utilizado (Ex: LOTE-ABC-2026):")
                    obs_extras = st.text_area("Observações Extras (Opcional):")
                    btn_gravar_prod = st.form_submit_button("Gravar Teste e Enviar para o CQ", use_container_width=True)
                    
                    if btn_gravar_prod and lote_digitado:
                        c = conn.cursor()
                        try:
                            id_prod_limpo = dict_fila[serial_sel]
                            c.execute("""
                                UPDATE produtos 
                                SET lote_placas = %s, quem_testou = %s, observacoes_extras = %s, quem_validou = 'PENDENTE'
                                WHERE id = %s
                            """, (lote_digitado.strip().upper(), st.session_state.usuario, obs_extras.strip().upper(), id_prod_limpo))
                            conn.commit()
                            st.success("✅ Dados de fabricação salvos com sucesso na nuvem!")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Erro ao salvar dados de fabricação: {e}")
            else:
                st.info("Não há nenhum equipamento aguardando montagem ou teste na fila atual.")

        # --- MÓDULO 3: CQ QUALIDADE ---
        elif "CQ Qualidade" in nome_aba:
            st.subheader("🔬 Inspeção de Qualidade e Auditoria")
            
            c = conn.cursor()
            c.execute("SELECT id, serial, numero_of, lote_placas FROM produtos WHERE quem_testou IS NOT NULL AND (quem_validou = 'PENDENTE' OR quem_validou = '')")
            fila_cq = c.fetchall()
            
            if fila_cq:
                dict_cq = {f"Serial: {r[1]} | OF: {r[2]}": r[0] for r in fila_cq}
                item_cq = st.selectbox("Selecione o Item para Auditar:", list(dict_cq.keys()))
                
                col_cq1, col_cq2 = st.columns(2)
                with col_cq1:
                    decisao_cq = st.radio("Resultado da Inspeção Final:", ["APROVADO", "REPROVADO"], horizontal=True)
                with col_cq2:
                    obs_cq = st.text_input("Laudo Técnico / Motivo do Reprovo (Obrigatório se Reprovado):")
                
                if st.button("Gravar Laudo de CQ", use_container_width=True):
                    id_cq_limpo = dict_cq[item_cq]
                    hj_cq = datetime.date.today().strftime("%d/%m/%Y")
                    c = conn.cursor()
                    
                    try:
                        if decisao_cq == "REPROVADO" and not obs_cq:
                            st.error("É obrigatório descrever a falha para gerar o reprovo!")
                        else:
                            status_final = st.session_state.usuario if decisao_cq == "APROVADO" else "REPROVADO_CQ"
                            c.execute("UPDATE produtos SET quem_validou = %s, observacoes_extras = %s WHERE id = %s", (status_final, obs_cq.strip().upper(), id_cq_limpo))
                            c.execute("INSERT INTO resultados_inspecao (produto_id, nome_inspecao, resultado, data_inspecao) VALUES (%s, 'INSPECAO_GERAL', %s, %s)", (id_cq_limpo, decisao_cq, hj_cq))
                            conn.commit()
                            st.success("📋 Laudo final gravado com sucesso!")
                            st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Erro ao gravar laudo de CQ: {e}")
            else:
                st.info("Nenhum equipamento aguardando auditoria do CQ no momento.")

        # --- MÓDULO 4: EXPEDIÇÃO ---
        elif "Expedição" in nome_aba:
            st.subheader("🚚 Faturamento Comercial e Despacho de Notas Fiscais")
            
            c = conn.cursor()
            c.execute("SELECT serial, numero_of, lote_placas, quem_validou FROM produtos WHERE quem_validou IS NOT NULL AND quem_validou != 'PENDENTE' AND quem_validou != 'REPROVADO_CQ'")
            itens_liberados = c.fetchall()
            
            if itens_liberados:
                st.write("Equipamentos liberados para faturamento comercial:")
                st.dataframe(itens_liberados, column_config={
                    "0": "Número Serial", "1": "Ordem de Fab (OF)", "2": "Lote Utilizado", "3": "Inspetor Responsável"
                }, use_container_width=True)
            else:
                st.info("Nenhum equipamento liberado pelo controle de qualidade aguardando faturamento.")

        # --- MÓDULO 5: CONFIGURAÇÕES ADM ---
        elif "Configurações" in nome_aba:
            st.subheader("🔑 Painel de TI e Configurações Administrativas")
            st.write("Visualize o total de registros salvos diretamente no cluster serverless do Neon:")
            
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM produtos")
            total_prod = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM usuarios")
            total_user = c.fetchone()[0]
            
            col_card1, col_card2 = st.columns(2)
            col_card1.metric("Equipamentos Rastreados", total_prod)
            col_card2.metric("Usuários Ativos no Sistema", total_user)
