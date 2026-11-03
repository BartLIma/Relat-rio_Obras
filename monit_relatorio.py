import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA (Layout padrão expansível)
st.set_page_config(page_title="Relatório Geral de Obras", layout="wide")
st.title("🏗️ Monitoramento - Relatório Geral de Obras")

@st.cache_data
def carregar_dados():
    # CORREÇÃO: Força colunas problemáticas a serem lidas estritamente como TEXTO (string)
    tipos_colunas = {
        "IBGE": str,
        "CNPJ": str,
        "Número da proposta": str,
        "Ano do cadastro": str,
        "Ano da proposta": str
    }
    
    # Carrega a planilha mapeando os tipos e usando ponto e vírgula
    df = pd.read_csv("relatorio_obras.csv", encoding="utf-8", sep=";", dtype=tipos_colunas)
    
    # Remove espaços invisíveis do início e fim de todos os cabeçalhos
    df.columns = df.columns.str.strip()
    
    # Limpa valores nulos ou esquisitos transformando códigos em strings limpas
    if "IBGE" in df.columns:
        df["IBGE"] = df["IBGE"].astype(str).str.split('.').str[0].str.replace('nan', '')
    if "CNPJ" in df.columns:
        df["CNPJ"] = df["CNPJ"].astype(str).str.split('.').str[0].str.replace('nan', '')
    
    # Padroniza as colunas de busca para evitar erros com espaços ou caixa alta/baixa
    if "Município" in df.columns:
        df["Muni_Busca"] = df["Município"].astype(str).str.upper().str.strip()
    if "Número da proposta" in df.columns:
        df["Prop_Busca"] = df["Número da proposta"].astype(str).str.strip()
        
    return df

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
    
    # 6. GERAÇÃO DE MENSAGEM PARA COPIAR (Substituído st.copy_to_clipboard por st.code)
    st.subheader("📝 Gerador de Resumo para Cópia")
    st.markdown("Selecione uma obra abaixo e use o botão de cópia automática no canto superior direito do bloco de texto.")
    
    # Caixa de seleção mapeada com 'Estabelecimento' para identificação rápida
    opcoes_obras = df_filtrado["Número da proposta"].astype(str) + " - " + df_filtrado["Estabelecimento"].astype(str)
    obra_selecionada_index = st.selectbox("Escolha a obra específica para copiar os dados:", opcoes_obras.index, format_func=lambda x: opcoes_obras[x])
    
    # Extrai a linha selecionada para montar o texto
    linha = df_filtrado.loc[obra_selecionada_index]
    
    # Montagem do texto estruturado utilizando os campos reais da imagem
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

    # O componente st.code adiciona automaticamente o botão flutuante "Copy" compatível com a nuvem
    st.code(texto_resumo, language="text")

    # 7. MONTAGEM DO MAPA VIA GPS (Com tratamento de texto e correção para busca por proposta individual)
    col_lat = "Latitude"
    col_lon = "Longitude"
    
    if col_lat in df_filtrado.columns and col_lon in df_filtrado.columns:
        st.subheader("📍 Geolocalização das Obras (GPS)")
        
        # Cria cópia para tratar strings sem quebrar a tabela original
        dados_mapa = df_filtrado.dropna(subset=[col_lat, col_lon]).copy()
        
        # Converte para texto e limpa vírgulas pontuais vindas do Excel brasileiro
        dados_mapa[col_lat] = dados_mapa[col_lat].astype(str).str.replace(",", ".", regex=False).str.strip()
        dados_mapa[col_lon] = dados_mapa[col_lon].astype(str).str.replace(",", ".", regex=False).str.strip()
        
        # Força conversão para float numérico puro
        dados_mapa[col_lat] = pd.to_numeric(dados_mapa[col_lat], errors='coerce')
        dados_mapa[col_lon] = pd.to_numeric(dados_mapa[col_lon], errors='coerce')
        
        # Retira linhas que falharam na conversão do GPS
        dados_mapa = dados_mapa.dropna(subset=[col_lat, col_lon])
        
        if not dados_mapa.empty:
            df_mapa_streamlit = dados_mapa[[col_lat, col_lon]].rename(columns={col_lat: "lat", col_lon: "lon"})
            st.map(df_mapa_streamlit)
        else:
            st.warning("O registro selecionado não possui coordenadas numéricas de GPS válidas na planilha para exibição do mapa.")
    else:
        st.error("As colunas 'Latitude' e 'Longitude' não foram encontradas no arquivo CSV.")
else:
    st.warning("Nenhuma obra encontrada para os critérios de busca selecionados.")
