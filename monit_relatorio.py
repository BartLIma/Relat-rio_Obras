import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA (Layout padrão expansível)
st.set_page_config(page_title="Relatório Geral de Obras", layout="wide")
st.title("🏗️ Monitoramento - Relatório Geral de Obras")

# 2. CARREGAMENTO DOS DADOS
@st.cache_data
def carregar_dados():
    df = pd.read_csv("relatorio_obras.csv", encoding="utf-8")
    
    # Padroniza as colunas de busca para evitar erros com espaços ou letras maiúsculas/minúsculas
    if "Município" in df.columns:
        df["Muni_Busca"] = df["Município"].astype(str).str.upper().str.strip()
    if "Número da proposta" in df.columns:
        df["Prop_Busca"] = df["Número da proposta"].astype(str).str.strip()
        
    return df

try:
    df_obras = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar o arquivo 'relatorio_obras.csv': {e}")
    st.stop()

# 3. PAINEL DE FILTROS NA BARRA LATERAL
st.sidebar.header("Filtros de Pesquisa")

# Busca por Município
lista_municipios = sorted(df_obras["Município"].dropna().unique()) if "Município" in df_obras.columns else []
municipio_selecionado = st.sidebar.selectbox("Selecione o Município:", ["Todos"] + lista_municipios)

# Busca por Número da Proposta
proposta_digitada = st.sidebar.text_input("Digite o Número da Proposta:").strip()

# 4. APLICAÇÃO DA LÓGICA DE FILTRAGEM
df_filtrado = df_obras.copy()

if municipio_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Município"] == municipio_selecionado]

if proposta_digitada:
    df_filtrado = df_filtrado[df_filtrado["Prop_Busca"] == proposta_digitada]

# 5. EXIBIÇÃO DE RESULTADOS E MÉTRICAS
if not df_filtrado.empty:
    
    # Bloco de Métricas Financeiras e Quantidade no topo da tela
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total de Obras Selecionadas", value=len(df_filtrado))
    with col2:
        if "Valor repassado" in df_filtrado.columns:
            total_repassado = pd.to_numeric(df_filtrado["Valor repassado"], errors='coerce').sum()
            st.metric(label="Total Repassado", value=f"R$ {total_repassado:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))
    with col3:
        if "Valor total pago" in df_filtrado.columns:
            total_pago = pd.to_numeric(df_filtrado["Valor total pago"], errors='coerce').sum()
            st.metric(label="Total Pago", value=f"R$ {total_pago:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))

    # Exibição da tabela de dados gerais
    st.subheader("📋 Informações Detalhadas das Obras")
    st.dataframe(df_filtrado)
    
    # 6. GERAÇÃO DE MENSAGEM PARA COPIAR
    st.subheader("📝 Gerador de Resumo para Cópia")
    st.markdown("Selecione uma obra abaixo para gerar um texto de resumo formatado pronto para ser copiado.")
    
    # Caixa de seleção caso o filtro traga mais de uma obra
    opcoes_obras = df_filtrado["Número da proposta"].astype(str) + " - " + df_filtrado["Nome da unidade"].astype(str)
    obra_selecionada_index = st.selectbox("Escolha a obra específica para copiar os dados:", opcoes_obras.index, format_func=lambda x: opcoes_obras[x])
    
    # Extrai a linha selecionada para montar o texto
    linha = df_filtrado.loc[obra_selecionada_index]
    
    # Montagem do texto estruturado
    texto_resumo = f"""*RELATÓRIO DE OBRA*
----------------------------------------
*Proposta:* {linha.get('Número da proposta', 'Não informado')}
*Unidade:* {linha.get('Nome da unidade', 'Não informado')}
*Município:* {linha.get('Município', 'Não informado')}
*Programa:* {linha.get('Programa', 'Não informado')}
*Modalidade:* {linha.get('Modalidade', 'Não informado')}
*Situação da Proposta:* {linha.get('Situação da proposta', 'Não informado')}
*Situação da Obra:* {linha.get('Situação da obra', 'Não informado')}
----------------------------------------
*Valores Financeiros:*
- Valor Repassado: R$ {linha.get('Valor repassado', 0)}
- Valor Total Pago: R$ {linha.get('Valor total pago', 0)}
----------------------------------------
*Coordenadas GPS:*
- Latitude: {linha.get('Latitude', 'Não cadastrada')}
- Longitude: {linha.get('Longitude', 'Não cadastrada')}"""

    # Área de visualização e botão de copiar oficial do Streamlit
    st.text_area("Texto formatado:", value=texto_resumo, height=280)
    st.copy_to_clipboard(texto_resumo, label="Copiar Texto para a Área de Transferência", icon="📋")

    # 7. MONTAGEM DO MAPA VIA GPS (Usando colunas nativas)
    col_lat = "Latitude"
    col_lon = "Longitude"
    
    if col_lat in df_filtrado.columns and col_lon in df_filtrado.columns:
        st.subheader("📍 Geolocalização das Obras (GPS)")
        
        dados_mapa = df_filtrado.dropna(subset=[col_lat, col_lon])
        dados_mapa[col_lat] = pd.to_numeric(dados_mapa[col_lat], errors='coerce')
        dados_mapa[col_lon] = pd.to_numeric(dados_mapa[col_lon], errors='coerce')
        dados_mapa = dados_mapa.dropna(subset=[col_lat, col_lon])
        
        if not dados_mapa.empty:
            df_mapa_streamlit = dados_mapa[[col_lat, col_lon]].rename(columns={col_lat: "lat", col_lon: "lon"})
            st.map(df_mapa_streamlit)
        else:
            st.warning("As obras encontradas não possuem coordenadas numéricas válidas para exibir no mapa.")
else:
    st.warning("Nenhuma obra encontrada para os critérios de busca selecionados.")
