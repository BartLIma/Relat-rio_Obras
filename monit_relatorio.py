import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA (Layout padrão expansível em alta resolução)
st.set_page_config(page_title="Relatório Geral de Obras", layout="wide")
st.title("🏗️ Monitoramento - Relatório Geral de Obras")

# 2. CARREGAMENTO DOS DADOS (Tratamento seguro e blindagem contra Overflow/Tipos)
@st.cache_data
def carregar_dados_seguro():
    # Força colunas com números longos ou códigos a serem lidas estritamente como TEXTO
    # Isso evita de forma definitiva o erro 'OverflowError' no pyarrow do Streamlit
    tipos_obrigatorios = {
        "IBGE": str,
        "CNPJ": str,
        "Número da proposta": str,
        "Ano do cadastro": str,
        "Ano da proposta": str
    }
    
    # Carrega a planilha usando ponto e vírgula como separador padrão do Excel nacional
    df = pd.read_csv("relatorio_obras.csv", encoding="utf-8", sep=";", dtype=tipos_obrigatorios)
    
    # Remove espaços invisíveis acidentais do início e fim de todos os cabeçalhos
    df.columns = df.columns.str.strip()
    
    # Limpa strings residuais de valores nulos para manter a interface limpa
    if "IBGE" in df.columns:
        df["IBGE"] = df["IBGE"].astype(str).str.replace('nan', '', case=False).str.strip()
    if "CNPJ" in df.columns:
        df["CNPJ"] = df["CNPJ"].astype(str).str.replace('nan', '', case=False).str.strip()
    
    # Cria colunas indexadas em letras maiúsculas e limpas para garantir buscas precisas
    if "Município" in df.columns:
        df["Muni_Busca"] = df["Município"].astype(str).str.upper().str.strip()
    if "Número da proposta" in df.columns:
        df["Prop_Busca"] = df["Número da proposta"].astype(str).str.strip()
        
    return df

# Executa o carregamento com tratamento de exceção amigável na tela
try:
    df_obras = carregar_dados_seguro()
except Exception as e:
    st.error(f"Erro crítico ao processar o arquivo 'relatorio_obras.csv': {e}")
    st.stop()

# 3. PAINEL DE FILTROS NA BARRA LATERAL
st.sidebar.header("Filtros de Pesquisa")

# Monta a lista de municípios removendo valores nulos para evitar falhas de ordenação
lista_municipios = sorted(df_obras["Município"].dropna().unique()) if "Município" in df_obras.columns else []
municipio_selecionado = st.sidebar.selectbox("Selecione o Município:", ["Todos"] + lista_municipios)

# Campo de busca por texto direto para número da Proposta
proposta_digitada = st.sidebar.text_input("Digite o Número da Proposta:").strip()

# 4. APLICAÇÃO DA LÓGICA FILTRADA NO DATAFRAME
df_filtrado = df_obras.copy()

# Aplica filtro de município se selecionado
if municipio_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Município"] == municipio_selecionado]

# Aplica filtro de proposta se digitado
if proposta_digitada:
    df_filtrado = df_filtrado[df_filtrado["Prop_Busca"] == proposta_digitada]

# 5. EXIBIÇÃO DE RESULTADOS E PAINEIS VISUAIS
if not df_filtrado.empty:
    
    # Bloco Superior de Métricas Consolidadas
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

    # Tabela detalhada tratada para renderização estável
    st.subheader("📋 Informações Detalhadas das Obras")
    st.dataframe(df_filtrado)
    
    # 6. GERAÇÃO DE TEXTO PARA CÓPIA (Utiliza st.code para máxima compatibilidade na nuvem)
    st.subheader("📝 Gerador de Resumo para Cópia")
    st.markdown("Selecione uma obra abaixo e use o botão flutuante **'Copy'** no canto superior direito da caixa preta.")
    
    # Cria rótulo combinando proposta e estabelecimento para facilitar a escolha do usuário
    opcoes_obras = df_filtrado["Número da proposta"].astype(str) + " - " + df_filtrado["Estabelecimento"].astype(str)
    obra_selecionada_index = st.selectbox("Escolha a obra específica para copiar os dados:", opcoes_obras.index, format_func=lambda x: opcoes_obras[x])
    
    # Extrai a linha exata selecionada
    linha = df_filtrado.loc[obra_selecionada_index]
    
    # Montagem estruturada da mensagem utilizando as colunas validadas da imagem
    texto_resumo = f"""*RELATÓRIO DE OBRA*
----------------------------------------
*Proposta:* {linha.get('Número da proposta', 'Não informado')}
*Estabelecimento:* {linha.get('Estabelecimento', 'Não informado')}
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

    # Exibe o painel estável de cópia com um clique
    st.code(texto_resumo, language="text")

    # 7. RENDERIZAÇÃO INTELIGENTE DO MAPA (Conversão de coordenadas padrão PT-BR)
    col_lat = "Latitude"
    col_lon = "Longitude"
    
    if col_lat in df_filtrado.columns and col_lon in df_filtrado.columns:
        st.subheader("📍 Geolocalização das Obras (GPS)")
        
        # Isola os dados de mapa para tratamento local seguro
        dados_mapa = df_filtrado.dropna(subset=[col_lat, col_lon]).copy()
        
        # Converte as strings trocando vírgulas por pontos decimais (Correção do Excel)
        dados_mapa[col_lat] = dados_mapa[col_lat].astype(str).str.replace(",", ".", regex=False).str.strip()
        dados_mapa[col_lon] = dados_mapa[col_lon].astype(str).str.replace(",", ".", regex=False).str.strip()
        
        # Transforma o texto limpo em coordenadas numéricas flutuantes (float)
        dados_mapa[col_lat] = pd.to_numeric(dados_mapa[col_lat], errors='coerce')
        dados_mapa[col_lon] = pd.to_numeric(dados_mapa[col_lon], errors='coerce')
        
        # Remove registros que falharam na validação numérica final
        dados_mapa = dados_mapa.dropna(subset=[col_lat, col_lon])
        
        if not dados_mapa.empty:
            # Renomeia os eixos locais para a sintaxe universal de mapas do Streamlit
            df_mapa_streamlit = dados_mapa[[col_lat, col_lon]].rename(columns={col_lat: "lat", col_lon: "lon"})
            st.map(df_mapa_streamlit)
        else:
            st.warning("O registro selecionado não possui coordenadas numéricas de GPS válidas para exibição do mapa.")
    else:
        st.error("As colunas 'Latitude' e 'Longitude' não foram encontradas no arquivo de dados.")
else:
    st.warning("Nenhuma obra encontrada para os critérios de busca selecionados.")
