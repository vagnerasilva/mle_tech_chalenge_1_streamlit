import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from collections import Counter
import os
import json
import logging
from dotenv import load_dotenv

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - streamlit - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== CONFIG ==========
st.set_page_config(
    page_title="API Logs Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo
sns.set_theme(style="darkgrid")
st.markdown("""
<style>
    .metric-container { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       padding: 20px; border-radius: 10px; color: white; }
</style>
""", unsafe_allow_html=True)

# ========== ENVIRONMENT ==========
load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
LOGS_ENDPOINT = f"{API_BASE_URL}/api_logs"

# ========== CONSTANTS ==========
LOGS_PER_PAGE = 2  # Número de logs por requisição
LOGS_TIMEOUT = 100  # Timeout padrão em segundos para requisições à API

# ========== CACHE ==========
@st.cache_data(ttl=300)  # Cache por 5 minutos
def fetch_logs(limit: int = LOGS_PER_PAGE, offset: int = 0, timeout: int = LOGS_TIMEOUT):
    """Busca logs da API com paginação e timeout configurável"""
    logger.info(f"🔍 Buscando logs da API - limit: {limit}, offset: {offset}, timeout: {timeout}s")
    try:
        params = {"limit": limit, "offset": offset}
        response = requests.get(LOGS_ENDPOINT, params=params, timeout=timeout)
        response.raise_for_status()
        logs = response.json()
        logger.info(f"✅ Logs obtidos com sucesso! Total: {len(logs)} registros")
        return logs
    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout após {timeout}s: A API demorou muito para responder")
        st.error(f"⏱️ Timeout após {timeout}s: A API demorou muito para responder.")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro ao conectar à API: {e}")
        st.error(f"❌ Erro ao conectar à API: {e}")
        return []

def load_mock_data():
    """Carrega dados mockados do arquivo JSON"""
    logger.info("📋 Carregando dados mock do json_mock.json")
    # Suporta vários nomes comuns (novo.json, json_mock.json)
    candidates = ["novo.json"]
    path = None
    for c in candidates:
        if os.path.exists(c):
            path = c
            break
    if not path:
        logger.error("❌ Arquivo de mock não encontrado (procurado: novo.json, json_mock.json)")
        st.error("❌ Arquivo de mock não encontrado (novo.json ou json_mock.json)")
        return []

    # Tentar decodificar com as codificações mais prováveis, cair para 'replace' se necessário
    encodings = ["utf-8", "cp1252", "latin-1"]
    last_exc = None
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                data = json.load(f)
                logger.info(f"✅ Dados mock carregados! (encoding={enc}) Total: {len(data)} registros")
                return data
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            last_exc = e
            logger.debug(f"Falha ao ler {path} com encoding={enc}: {e}")
            continue

    # Último recurso: abrir em binário e decodificar com replacement para garantir texto válido
    try:
        with open(path, "rb") as f:
            raw = f.read()
        text = raw.decode("utf-8", errors="replace")
        data = json.loads(text)
        # salvar uma cópia limpa para futuras execuções
        clean_path = os.path.splitext(path)[0] + "_clean.json"
        with open(clean_path, "w", encoding="utf-8") as cf:
            cf.write(text)
        logger.info(f"✅ Dados mock carregados via fallback e salvos em {clean_path}. Total: {len(data)} registros")
        return data
    except Exception as e:
        logger.error(f"❌ Não foi possível ler/parsear {path}: {e}")
        st.error(f"❌ Erro ao carregar dados mock: {e}")
        if last_exc:
            logger.debug(f"Erro original: {last_exc}")
        return []

def convert_logs_to_dataframe(logs):
    """Converte logs JSON em DataFrame"""
    logger.info(f"📊 Convertendo {len(logs)} logs para DataFrame")
    if not logs:
        logger.warning("⚠️ Nenhum log para converter")
        return pd.DataFrame()
    
    data = []
    for log in logs:
        data.append({
            'ID': log.get('id'),
            'Método': log.get('method'),
            'Path': log.get('path'),
            'Status': log.get('status_code'),
            'Tempo (ms)': round(log.get('process_time', 0) * 1000, 2),
            'IP': log.get('ip_address'),
            'Data': pd.to_datetime(log.get('created_at'))
        })
    df = pd.DataFrame(data)
    logger.info(f"✅ DataFrame criado com sucesso! Shape: {df.shape}")
    return df

# ========== LAYOUT ==========
st.title("📊 Dashboard de Logs da API")
st.markdown("Visualização e análise dos logs de requisições da API")

# Sidebar (definir ANTES de usar)
with st.sidebar:
    st.header("⚙️ Controles")
    
    # Mostrar qual ambiente está sendo usado
    if "localhost" in API_BASE_URL or "127.0.0.1" in API_BASE_URL:
        st.success("✅ Ambiente: Local")
    else:
        st.info("🌐 Ambiente: Produção")
    
    st.caption(f"API: {API_BASE_URL}")
    
    st.markdown("---")
    
    # Controle de limite de logs
    logs_limit = st.slider("Limite de Logs", min_value=2, max_value=5000, value=2, step=1)
    
    # Tempo de espera (timeout) configurável
    logs_timeout = st.number_input("Timeout (s)", min_value=1, max_value=120, value=LOGS_TIMEOUT, step=1,
                                   help="Tempo máximo (em segundos) para esperar a resposta da API")
    
    st.markdown("---")
    
    # Seletor de fonte de dados
    # Detectar se está em ambiente local e usar Mock por padrão
    is_local = "localhost" in API_BASE_URL or "127.0.0.1" in API_BASE_URL
    default_source_index = 1 if is_local else 0  # 1 = Mock, 0 = API
    
    logger.info(f"🌍 Ambiente: {'LOCAL' if is_local else 'PRODUÇÃO'} - Fonte padrão: {'📋 Mock' if is_local else '🔗 API'}")
    
    data_source = st.radio(
        "📊 Fonte de Dados",
        ["🔗 API", "📋 Mock"],
        index=default_source_index,
        help="Escolha entre dados reais da API ou dados mockados para teste"
    )
    
    st.markdown("---")
    
    refresh = st.button("🔄 Atualizar Dados", use_container_width=True)

    # Inicializar last_refresh se não existir
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = datetime.now()

    # Inicializar fetch_params na session com valores padrão (executa na primeira carga)
    if "fetch_params" not in st.session_state:
        st.session_state.fetch_params = {
            "limit": logs_limit,
            "timeout": LOGS_TIMEOUT,
            "data_source": ("📋 Mock" if default_source_index == 1 else "🔗 API")
        }

    # Ao apertar atualizar, gravar os valores selecionados em session_state.fetch_params
    if refresh:
        st.session_state.fetch_params = {
            "limit": logs_limit,
            "timeout": logs_timeout,
            "data_source": data_source
        }
        st.cache_data.clear()
        st.session_state.last_refresh = datetime.now()
        # Tentar forçar rerun. Se `experimental_rerun` não existir na versão do Streamlit,
        # usar um fallback que altera query params para acionar uma nova execução.
        try:
            if hasattr(st, "experimental_rerun"):
                st.experimental_rerun()
            else:
                raise AttributeError("experimental_rerun not available")
        except Exception:
            # Fallback: toggle a session key e set_query_params para forçar reload
            st.session_state["_rerun_trigger"] = st.session_state.get("_rerun_trigger", 0) + 1
            try:
                # Nova API: atribuir a `st.query_params` para atualizar os query params
                try:
                    current_qp = dict(st.query_params)
                except Exception:
                    current_qp = {}
                current_qp["_rs"] = str(st.session_state["_rerun_trigger"])
                try:
                    st.query_params = current_qp
                except Exception:
                    # última alternativa: apenas escrever um aviso (não trava a UI)
                    logger.warning("Não foi possível atualizar st.query_params; atualize a página manualmente.")
            except Exception:
                logger.warning("Não foi possível forçar rerun automaticamente; atualize a página manualmente.")

    st.markdown(f"**Última atualização:** {st.session_state.last_refresh.strftime('%H:%M:%S')}")

# ========== MAIN ==========
# Buscar dados usando os parâmetros salvos em session_state.fetch_params
params = st.session_state.get('fetch_params', {})
p_limit = params.get('limit', LOGS_PER_PAGE)
p_timeout = params.get('timeout', LOGS_TIMEOUT)
p_data_source = params.get('data_source', ("📋 Mock" if default_source_index == 1 else "🔗 API"))

if p_data_source == "📋 Mock":
    st.sidebar.success("📋 Usando dados MOCK")
    logger.info("=" * 60)
    logger.info("🎯 INICIANDO CARREGAMENTO DE DADOS MOCK")
    logger.info("=" * 60)
    logs = load_mock_data()
else:
    st.sidebar.info("🔗 Usando dados da API")
    logger.info("=" * 60)
    logger.info("🎯 INICIANDO CARREGAMENTO DE DADOS DA API")
    logger.info("=" * 60)
    logger.info(f"⏳ Usando timeout de {p_timeout}s para a requisição")
    logs = fetch_logs(limit=p_limit, offset=0, timeout=int(p_timeout))

df = convert_logs_to_dataframe(logs)

# Debug: mostrar parâmetros usados (aplicados)
st.sidebar.info(f"📡 Parâmetros aplicados — Fonte: {p_data_source} | Limit: {p_limit} | Timeout: {p_timeout}s")
logger.info("=" * 60)

if df.empty:
    logger.warning("⚠️ DataFrame vazio - nenhum log encontrado")
    st.warning("⚠️ Nenhum log encontrado")
    st.stop()

logger.info(f"📈 Dashboard carregado - Total de linhas: {len(df)}")

# ========== METRICS ==========
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📝 Total de Requisições", len(df))

with col2:
    avg_time = df['Tempo (ms)'].mean()
    st.metric("⏱️ Tempo Médio", f"{avg_time:.2f} ms")

with col3:
    success_count = len(df[df['Status'] == 200])
    st.metric("✅ Requisições OK", success_count)

with col4:
    error_count = len(df[df['Status'] >= 400])
    st.metric("❌ Erros", error_count)

# ========== FILTERS ==========
st.markdown("---")
st.subheader("🔎 Filtros")

col1, col2, col3 = st.columns(3)

with col1:
    methods = st.multiselect("Método HTTP", df['Método'].unique(), default=df['Método'].unique())

with col2:
    status_filter = st.multiselect("Status Code", sorted(df['Status'].unique()), 
                                   default=sorted(df['Status'].unique()))

with col3:
    date_range = st.date_input("Período", value=(df['Data'].min().date(), df['Data'].max().date()))

# Aplicar filtros
df_filtered = df[
    (df['Método'].isin(methods)) & 
    (df['Status'].isin(status_filter)) &
    (df['Data'].dt.date >= date_range[0]) &
    (df['Data'].dt.date <= date_range[1])
]

st.info(f"📌 Mostrando {len(df_filtered)} de {len(df)} registros")

# ========== VISUALIZATIONS ==========
st.markdown("---")
st.subheader("📈 Visualizações")

col1, col2 = st.columns(2)

# Gráfico 1: Requisições por Método
with col1:
    st.markdown("#### Requisições por Método HTTP")
    method_counts = df_filtered['Método'].value_counts()
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe']
    ax1.bar(method_counts.index, method_counts.values, color=colors[:len(method_counts)])
    ax1.set_ylabel("Quantidade")
    ax1.set_xlabel("Método")
    st.pyplot(fig1)

# Gráfico 2: Status Codes
with col2:
    st.markdown("#### Distribuição de Status Codes")
    status_counts = df_filtered['Status'].value_counts()
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    status_colors = ['#00d4ff' if s == 200 else '#ff6b6b' for s in status_counts.index]
    ax2.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%', colors=status_colors)
    ax2.set_title("Status Codes")
    st.pyplot(fig2)

# Gráfico 3: Tempo de Resposta
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Tempo de Resposta por Path (Top 10)")
    path_times = df_filtered.groupby('Path')['Tempo (ms)'].mean().nlargest(10)
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    ax3.barh(range(len(path_times)), path_times.values, color='#667eea')
    ax3.set_yticks(range(len(path_times)))
    ax3.set_yticklabels(path_times.index, fontsize=9)
    ax3.set_xlabel("Tempo Médio (ms)")
    st.pyplot(fig3)

# Gráfico 4: Top IPs
with col2:
    st.markdown("#### Top 10 IPs com Mais Requisições")
    top_ips = df_filtered['IP'].value_counts().head(10)
    fig4, ax4 = plt.subplots(figsize=(10, 6))
    ax4.barh(range(len(top_ips)), top_ips.values, color='#764ba2')
    ax4.set_yticks(range(len(top_ips)))
    ax4.set_yticklabels(top_ips.index, fontsize=9)
    ax4.set_xlabel("Quantidade")
    st.pyplot(fig4)

# ========== ADDITIONAL VISUALIZATIONS ==========
st.markdown("---")
st.subheader("📉 Análises Adicionais")

col1, col2, col3 = st.columns(3)

# Gráfico 5: Estatísticas de Tempo de Resposta
with col1:
    st.markdown("#### Estatísticas de Tempo de Resposta")
    min_time = df_filtered['Tempo (ms)'].min()
    max_time = df_filtered['Tempo (ms)'].max()
    avg_time = df_filtered['Tempo (ms)'].mean()
    
    fig5, ax5 = plt.subplots(figsize=(8, 5))
    stats_labels = ['Mínimo', 'Máximo', 'Média']
    stats_values = [min_time, max_time, avg_time]
    colors_stats = ['#4facfe', '#ff6b6b', '#667eea']
    bars = ax5.bar(stats_labels, stats_values, color=colors_stats)
    ax5.set_ylabel("Tempo (ms)")
    ax5.set_title("Min/Max/Média de Resposta")
    # Adicionar valores nas barras
    for bar, value in zip(bars, stats_values):
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.2f}',
                ha='center', va='bottom', fontsize=10)
    st.pyplot(fig5)

# Gráfico 6: Paths Mais Acessados
with col2:
    st.markdown("#### Paths Mais Acessados")
    path_counts = df_filtered['Path'].value_counts().head(8)
    fig6, ax6 = plt.subplots(figsize=(8, 5))
    ax6.barh(range(len(path_counts)), path_counts.values, color='#f093fb')
    ax6.set_yticks(range(len(path_counts)))
    ax6.set_yticklabels(path_counts.index, fontsize=9)
    ax6.set_xlabel("Acessos")
    st.pyplot(fig6)

# Gráfico 7: Taxa de Sucesso vs Erro
with col3:
    st.markdown("#### Taxa de Sucesso vs Erro")
    success = len(df_filtered[df_filtered['Status'] < 400])
    error = len(df_filtered[df_filtered['Status'] >= 400])
    
    fig7, ax7 = plt.subplots(figsize=(8, 5))
    sizes = [success, error]
    labels = [f'Sucesso\n({success})', f'Erro\n({error})']
    colors_pie = ['#00d4ff', '#ff6b6b']
    explode = (0.05, 0.05)
    ax7.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors_pie, explode=explode)
    ax7.set_title("Taxa de Sucesso")
    st.pyplot(fig7)

# ========== TIMELINE ==========
st.markdown("---")
st.subheader("⏰ Timeline de Requisições")

# Criar timeline por hora
df_filtered['Hora'] = df_filtered['Data'].dt.floor('h')
timeline_data = df_filtered.groupby('Hora').size()

if len(timeline_data) > 0:
    fig8, ax8 = plt.subplots(figsize=(12, 5))
    ax8.plot(timeline_data.index, timeline_data.values, marker='o', color='#667eea', linewidth=2, markersize=8)
    ax8.fill_between(timeline_data.index, timeline_data.values, alpha=0.3, color='#667eea')
    ax8.set_xlabel("Hora")
    ax8.set_ylabel("Número de Requisições")
    ax8.set_title("Requisições por Hora")
    ax8.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    st.pyplot(fig8)
else:
    st.info("📭 Dados insuficientes para timeline")

# ========== DATA TABLE ==========
st.markdown("---")
st.subheader("📋 Dados Detalhados")

# Ordenação
sort_col = st.selectbox("Ordenar por", df_filtered.columns)
sort_order = st.radio("Ordem", ["Crescente", "Decrescente"], horizontal=True)
ascending = sort_order == "Crescente"

df_sorted = df_filtered.sort_values(by=sort_col, ascending=ascending)

st.dataframe(df_sorted, use_container_width=True)

# Download
st.markdown("---")
col1, col2 = st.columns([1, 1])

with col1:
    csv = df_sorted.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"api_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

with col2:
    st.info("💡 Dados atualizados a cada 5 minutos. Clique em 'Atualizar Dados' para forçar refresh.")
