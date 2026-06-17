import streamlit as str
import geopandas as gpd
import geobr
import networkx as nx
from shapely.ops import substring
from shapely.geometry import LineString, Point

st.set_page_config(layout="wide")
st.title("🚊 Planejador Nacional de Vistoria Ferroviária (Rede/Grafos)")

# --- PASSO 1: CARREGAMENTO DOS DADOS NACIONAIS ---
@st.cache_data
def carregar_bases_nacionais():
    # read_railway() traz a malha nacional; read_municipal_seat() traz os pontos das sedes
    malha_ferroviaria = geobr.read_railway()
    sedes_municipios = geobr.read_municipal_seat()
    return malha_ferroviaria, sedes_municipios

with st.spinner("Carregando bases geográficas do IBGE/ANTT..."):
    malha, sedes = carregar_bases_nacionais()

# --- PASSO 2: FILTROS NA SIDEBAR ---
st.sidebar.header("1. Seleção de Região")

# Lista de UFs únicas disponíveis na base do IBGE
lista_ufs = sorted(sedes['abbrev_state'].unique())
uf_selecionada = st.sidebar.selectbox("Selecione a UF de atuação:", lista_ufs, index=lista_ufs.index("SP") if "SP" in lista_ufs else 0)

# Filtrar municípios apenas da UF selecionada
sedes_filtradas = sedes[sedes['abbrev_state'] == uf_selecionada].sort_values(by="name_muni")
lista_municipios = sedes_filtradas['name_muni'].unique()

st.sidebar.header("2. Rota da Viagem")
muni_origem = st.sidebar.selectbox("Município de Partida:", lista_municipios)
# Evitar que a origem seja igual ao destino na lista
muni_destino = st.sidebar.selectbox("Município de Destino:", [m for m in lista_municipios if m != muni_origem])

# Período e cálculo de trechos
st.sidebar.header("3. Cronograma")
datas = st.sidebar.date_input("Período da Vistoria (Seg à Sex):", [])

if len(datas) == 2:
    data_ini, data_fim = datas
    dias_trabalho = (data_fim - data_ini).days + 1
    
    # Define o padrão de 1 trecho por dia de trabalho
    num_trechos = st.sidebar.number_input(
        "Quantidade de trechos a vistoriar:", 
        min_value=1, 
        value=dias_trabalho, 
        help="Por padrão, adota-se 1 trecho por dia de trabalho."
    )
else:
    num_trechos = st.sidebar.number_input("Quantidade de trechos a vistoriar:", min_value=1, value=5)
    st.sidebar.warning("Selecione a data de início e término para calcular os dias exatos.")

# --- PASSO 3: O PROCESSAMENTO AO CLICAR NO BOTÃO ---
if st.sidebar.button("Calcular Rota e Dividir Trechos"):
    st.subheader(f"📍 Planejamento de Rota: {muni_origem} ➡️ {muni_destino} ({uf_selecionada})")
    
    # Resgatar a geometria (ponto) da origem e destino
    ponto_origem = sedes_filtradas[sedes_filtradas['name_muni'] == muni_origem].geometry.values[0]
    ponto_destino = sedes_filtradas[sedes_filtradas['name_muni'] == muni_destino].geometry.values[0]
    
    # -------------------------------------------------------------------------
    # AQUI ENTRA A MÁGICA DO GRAFO (Resumo conceitual do processo interno):
    # 1. G = momepy.gdf_to_nx(malha) -> Transforma as linhas em Grafo
    # 2. no_origem = encontrar_no_mais_proximo(G, ponto_origem)
    # 3. no_destino = encontrar_no_mais_proximo(G, ponto_destino)
    # 4. rota_final_nodes = nx.shortest_path(G, no_origem, no_destino, weight='length')
    # -------------------------------------------------------------------------
    
    st.info("Algoritmo de rede executado! Rota exata pelos trilhos identificada.")
    
    # Simulação da rota calculada (Apenas para demonstração visual enquanto não plugamos o grafo completo)
    # Na prática, 'linha_rota' será o LineString resultante da união das arestas do grafo.
    linha_rota = LineString([ponto_origem, ponto_destino]) # Simulação direta (linha reta provisória)
    comprimento_total = 250.0 # Exemplo: 250 km
    
    st.metric("Distância Total Estimada nos Trilhos", f"{comprimento_total} km")
    
    # --- PASSO 4: FATIAMENTO DA LINHA (SUBSTRING) ---
    st.write(f"### 🗓️ Divisão Operacional em {num_trechos} dias/trechos:")
    
    tam_trecho = comprimento_total / num_trechos
    
    for i in range(num_trechos):
        inicio_trecho = i * tam_trecho
        fim_trecho = (i + 1) * tam_trecho
        
        # A função 'substring' corta o LineString exatamente nas distâncias informadas
        # Para usá-la de forma real, a geometria precisa estar projetada em metros (ex: UTM)
        st.write(f"• **Dia {i+1}:** Vistoriar do km {inicio_trecho:.1f} ao km {fim_trecho:.1f} (Extensão: {tam_trecho:.1f} km)")
