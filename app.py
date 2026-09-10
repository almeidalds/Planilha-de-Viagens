import sys
import asyncio
import base64
from pathlib import Path
import io
import re

if sys.platform == "win32":
    try: asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except: pass

import streamlit as st
import pandas as pd
import requests
from datetime import date

from modelos import aplicar_design, normalizar_texto
from logistica import definir_transporte

st.set_page_config(page_title="Viagens | CTM", layout="wide")

st.markdown("""
<style>
    .stApp { background: #f7f9fb; }
    [data-testid="stSidebar"] { background: #1e2f50; border-right: 1px solid #14233d; }
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span { color: #ffffff; }
    [data-testid="stSidebar"] [data-baseweb="select"] * { color: #17324d; }
    [data-testid="stSidebar"] input { color: #17324d; }
    [data-testid="stSidebar"] [data-baseweb="input"] input,
    [data-testid="stSidebar"] [data-baseweb="input"] span,
    [data-testid="stSidebar"] [data-baseweb="input"] button { color: #000000 !important; }
    [data-testid="stSidebar"] [data-testid="stDateInput"] input,
    [data-testid="stSidebar"] [data-testid="stDateInput"] button,
    [data-testid="stSidebar"] [data-testid="stDateInput"] [role="button"] *,
    [data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="input"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    [data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="input"] {
        background: #ffffff !important;
    }
    [data-testid="stSidebar"] [data-testid="stDateInput"] div[data-baseweb="input"] *,
    [data-testid="stSidebar"] [data-testid="stDateInput"] [role="textbox"] *,
    [data-testid="stSidebar"] [data-testid="stDateInput"] input::placeholder {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebar"] [data-testid="stDateInput"] label {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] button { color: #ffffff; }
    [data-testid="stSidebar"] > div:first-child { padding-top: 130px; }
    .sidebar-logo { position: fixed; left: 18px; top: 18px; width: 92px; z-index: 10; }
    .sidebar-logo img { display: block; width: 92px; height: 92px; object-fit: contain; border-radius: 8px; }
    .topbar { display: flex; align-items: center; padding: .4rem 0 1.2rem; border-bottom: 1px solid #d8e1e8; margin-bottom: 1.4rem; }
    .brand-mark { width: 62px; height: 62px; display: grid; place-items: center; background: #173b63; color: white; border-radius: 10px; font-weight: 800; font-size: 1.15rem; letter-spacing: .04em; }
    .brand-title { color: #17324d; font-size: 1.7rem; font-weight: 750; line-height: 1.1; }
    .brand-subtitle { color: #637587; margin-top: .25rem; font-size: .92rem; }
    .section-title { color: #17324d; font-size: 1.15rem; font-weight: 700; margin: .3rem 0 .8rem; }
    div[data-testid="stMetric"] { background: white; border: 1px solid #d8e1e8; padding: .8rem; border-radius: 8px; }
    div[data-testid="stDataFrame"] { border: 1px solid #d8e1e8; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)
# abaixo, coloque o caminho da pastar como abaixo!
PASTA_BASE = Path(r"C:\Users\Almeidalds\OneDrive - Church of Jesus Christ\Paulo Cezar Sousa's files - Planilha de Viagens - (PYTHON, NÃO MEXE AMIGA)")
PASTA_VOOS = PASTA_BASE / "voo_semanais"
LOGO_PATH = Path(__file__).with_name("logo.png")
LINK_MASTER = "https://churchofjesuschrist-my.sharepoint.com/:x:/g/personal/sousapco_churchofjesuschrist_org/cQrxxNU8XT-LTZgFFHcE6t4jEgUCisL4Wj83Jj79aQE6Xh1i0A?download=1"

def localizar_cabecalho(df):
    """Encontra os cabeçalhos varrendo linhas e ignorando títulos."""
    for i in range(min(15, len(df))):
        linha = df.iloc[i].astype(str).str.upper().str.strip()
        celulas_preenchidas = [v for v in linha.values if v != 'NAN' and v != '']
        if any("MISSION" in val or "TIPO" in val or "NOME" in val for val in celulas_preenchidas) and len(celulas_preenchidas) >= 3:
            df.columns = df.iloc[i].astype(str).str.strip()
            df = df.iloc[i+1:].reset_index(drop=True)
            valid_cols = [c for c in df.columns if str(c).strip().upper() != 'NAN']
            return df[valid_cols]
    return df

def normalizar_nome_missionario(nome):
    """Usa a mesma chave para nomes no formato Nome Sobrenome e Sobrenome, Nome."""
    nome_normalizado = normalizar_texto(nome)
    if not nome_normalizado:
        return ""

    if "," in nome_normalizado:
        sobrenome, nomes = [parte.strip() for parte in nome_normalizado.split(",", 1)]
        return " ".join(f"{nomes} {sobrenome}".split())

    return " ".join(nome_normalizado.replace(",", " ").split())

def converter_data(valor):
    data = pd.to_datetime(valor, errors="coerce", format="mixed", dayfirst=True)
    return data.dt.normalize() if isinstance(data, pd.Series) else data.normalize()

def padronizar_colunas(df):
    """Mapeia colunas específicas da Master (Msny ID, Type, Country Home Unit) e dos voos"""
    col_map = {}
    seen = set()
    
    for col in df.columns:
        col_up = str(col).upper().strip()
        new_col = None
        
        # Mapeamento exato solicitado
        if "MSNY ID" in col_up:
            new_col = "ID"
        elif col_up == "TYPE":
            new_col = "Tipo"
        elif "COUNTRY HOME UNIT" in col_up:
            new_col = "Países"
        elif "MISSIONARY NAME" in col_up or "NOME DO MISSION" in col_up or "NOME DO PASSAGEIRO" in col_up or "NOME COMPLETO" in col_up or "MISSIONÁRIOS" in col_up or "MISSIONARIOS" in col_up:
            new_col = "Missionários"
        elif "MISSÂO" in col_up or "MISSÃO" in col_up or "MISSION ASSIGNED" in col_up or "MISSÕES" in col_up:
            new_col = "Missões"
        elif "CIA AEREA" in col_up:
            new_col = "CIA_AEREA_RAW"
        elif "DATA E HORARIO" in col_up:
            new_col = "DATA_RAW"
        elif "LOCALIZADOR" in col_up or "LOC CIA" in col_up:
            new_col = "Loc Cia"
        elif "COUNTRY" in col_up or "PAÍSES" in col_up or "PAISES" in col_up or "ORIGEM" in col_up:
            new_col = "Países"
            
        if new_col and new_col not in seen:
            col_map[col] = new_col
            seen.add(new_col)

    df = df.rename(columns=col_map)
    
    # CORTA TEXTOS MISTURADOS DOS ARQUIVOS DE VOOS
    if "DATA_RAW" in df.columns:
        df["Partida"] = df["DATA_RAW"].astype(str).apply(lambda x: re.search(r'Saída(.*?)(?:Data|$)', x.replace('\n', ''), re.IGNORECASE).group(1).strip() if re.search(r'Saída(.*?)(?:Data|$)', x.replace('\n', ''), re.IGNORECASE) else "")
        df["Chegada"] = df["DATA_RAW"].astype(str).apply(lambda x: re.search(r'Chegada(.*)', x.replace('\n', ''), re.IGNORECASE).group(1).strip() if re.search(r'Chegada(.*)', x.replace('\n', ''), re.IGNORECASE) else "")
    
    if "CIA_AEREA_RAW" in df.columns:
        df["Cia"] = df["CIA_AEREA_RAW"].astype(str).apply(lambda x: re.search(r'^([A-Za-z\s]+)', x).group(1).strip() if re.search(r'^([A-Za-z\s]+)', x) else x)
        df["Voo"] = df["CIA_AEREA_RAW"].astype(str).apply(lambda x: re.search(r'(\d+)$', x).group(1).strip() if re.search(r'(\d+)$', x) else "")
        
    return df

@st.cache_data(ttl=300)
def carregar_master_online(modo):
    resposta = requests.get(LINK_MASTER, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
    if resposta.status_code != 200: raise Exception("Falha na conexão online.")
    arq = io.BytesIO(resposta.content)

    abas = pd.read_excel(arq, sheet_name=None, header=None)
    nome_master = next((nome for nome in abas if nome.strip().upper() == "MASTER"), None)
    if nome_master is None:
        raise Exception("A aba MASTER não foi encontrada na planilha online.")

    nomes_abas = [nome_master] + [nome for nome in abas if nome != nome_master]
    tabelas_master = []
    for nome in nomes_abas:
        tabela = padronizar_colunas(localizar_cabecalho(abas[nome].copy()))
        if "Missionários" in tabela.columns:
            tabelas_master.append(tabela)

    if not tabelas_master:
        raise Exception("Nenhuma aba da master possui a coluna de missionários.")

    df = pd.concat(tabelas_master, ignore_index=True, sort=False)
    df["chave"] = df["Missionários"].apply(normalizar_nome_missionario)
    df = df[df["chave"] != ""].drop_duplicates(subset=["chave"], keep="first")

    for coluna in ["Tipo", "ID", "Países"]:
        if coluna not in df.columns:
            df[coluna] = ""

    return df

def ler_voos(caminho, modo):
    xls = pd.ExcelFile(caminho)
    abas = []
    
    if len(xls.sheet_names) == 1:
        df = pd.read_excel(caminho, sheet_name=0, header=None)
        return padronizar_colunas(localizar_cabecalho(df)), None
        
    for aba in xls.sheet_names:
        aba_up = aba.upper()
        if modo == "Chegadas" and ("CASA" in aba_up or "CTM" in aba_up or "CHEGADA" in aba_up or "SETEMBRO" in aba_up): abas.append(aba)
        elif modo == "Partidas" and ("MISS" in aba_up or "PARTIDA" in aba_up or "INTERNACIONAL" in aba_up or "NACIONAL" in aba_up): abas.append(aba)
            
    if not abas: return None, "Nenhuma página correspondente encontrada."
    
    df = pd.concat([pd.read_excel(caminho, sheet_name=a, header=None) for a in abas], ignore_index=True)
    return padronizar_colunas(localizar_cabecalho(df)), None


# --- INTERFACE ---
st.markdown("""
<div class="topbar">
    <div>
        <div class="brand-title">Planilhas de Viagens</div>
        <div class="brand-subtitle">Controle de chegadas e partidas</div>
    </div>
</div>
""", unsafe_allow_html=True)

if LOGO_PATH.exists():
    logo_base64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    st.sidebar.markdown(
        f'<div class="sidebar-logo"><img src="data:image/png;base64,{logo_base64}" alt="Logo CTM"></div>',
        unsafe_allow_html=True,
    )
else:
    st.sidebar.markdown('<div class="sidebar-logo"><div class="brand-mark">CTM</div></div>', unsafe_allow_html=True)

st.sidebar.markdown("## Configuração")
st.sidebar.caption("Defina os filtros e processe os dados quando estiver pronto.")
modo = st.sidebar.radio("Fluxo de logística", ["Chegadas", "Partidas"], horizontal=True)

if not PASTA_VOOS.exists(): st.stop()
arquivos = list(PASTA_VOOS.glob("*.xls*"))
if not arquivos: st.stop()

arquivo_escolhido = st.sidebar.selectbox("Planilha de voos", arquivos, format_func=lambda x: x.name)

periodo = st.sidebar.date_input(
    "Período de saída/chegada",
    value=(date.today(), date.today()),
    min_value=date(2020, 1, 1),
    max_value=date(2035, 12, 31),
    format="DD/MM/YYYY"
)
if isinstance(periodo, tuple):
    data_inicio, data_fim = periodo
else:
    data_inicio = data_fim = periodo

st.sidebar.caption(f"Período selecionado: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")

if st.sidebar.button("Processar Dados", type="primary"):
    with st.spinner("Decodificando textos, estruturando design e calculando frotas..."):
        df_master = carregar_master_online(modo)
        df_voos, erro = ler_voos(arquivo_escolhido, modo)

        if erro:
            st.error(erro)
            st.stop()

        inicio = pd.Timestamp(data_inicio)
        fim = pd.Timestamp(data_fim) + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)

        if "Missionários" not in df_voos.columns:
            st.error("❌ Não foi possível encontrar a coluna de Nomes nos voos.")
            st.stop()

        if "Missionários" not in df_master.columns:
            st.error("❌ Não foi possível encontrar a coluna de Nomes na MASTER.")
            st.stop()

        coluna_data_voo = "Chegada" if modo == "Chegadas" else "Partida"
        if coluna_data_voo not in df_voos.columns:
            st.error(f"A planilha de voos não possui a coluna de data '{coluna_data_voo}'.")
            st.stop()

        df_voos.dropna(subset=["Missionários"], inplace=True)
        df_master.dropna(subset=["Missionários"], inplace=True)
        df_voos["_data_periodo"] = converter_data(df_voos[coluna_data_voo])
        df_voos = df_voos[df_voos["_data_periodo"].between(inicio, fim)].copy()

        if df_voos.empty:
            st.warning("Nenhum missionário foi encontrado na planilha de voos para o período selecionado.")
            st.stop()

        df_voos["chave"] = df_voos["Missionários"].apply(normalizar_nome_missionario)
        df_master["chave"] = df_master["Missionários"].apply(normalizar_nome_missionario)
        df_voos["_tem_voo"] = True

        # A planilha de voos define quem aparece; a master apenas complementa os dados.
        df_final = pd.merge(df_voos, df_master, on="chave", how="left")

        for coluna in ["Tipo", "ID", "Países"]:
            if coluna not in df_final.columns:
                df_final[coluna] = ""

        df_final["Status do Voo"] = df_final.get("_tem_voo", False).fillna(False).map(
            {True: "Voo confirmado", False: "Pendente de voo"}
        )

        # Prioridade absoluta para a Master preencher ID, Tipo e Países/Origem
        for col in ["Missionários", "Tipo", "Países", "ID", "Missões", "Loc Cia", "Partida", "Chegada", "Cia", "Voo"]:
            if col + "_x" in df_final.columns and col + "_y" in df_final.columns:
                df_final[col + "_x"] = df_final[col + "_x"].replace(r'^\s*$', None, regex=True)
                df_final[col + "_y"] = df_final[col + "_y"].replace(r'^\s*$', None, regex=True)

                # Master (_y) ganha prioridade para colunas oficiais do CTM
                if col in ["Tipo", "ID", "Países", "Missões"]:
                    df_final[col] = df_final[col + "_y"].combine_first(df_final[col + "_x"])
                else:
                    df_final[col] = df_final[col + "_x"].combine_first(df_final[col + "_y"])

            elif col not in df_final.columns:
                if col + "_x" in df_final.columns: df_final[col] = df_final[col + "_x"]
                elif col + "_y" in df_final.columns: df_final[col] = df_final[col + "_y"]
        
        # Em chegadas, País vira Origem
        if modo == "Chegadas" and "Países" in df_final.columns:
            df_final["Origem"] = df_final["Países"]

        col_agrupamento = "Chegada" if modo == "Chegadas" else "Partida"
        df_final["Quant."] = pd.NA
        df_final["Transportes"] = ""
        confirmados = df_final["Status do Voo"] == "Voo confirmado"
        if col_agrupamento in df_final.columns and "Voo" in df_final.columns and confirmados.any():
            df_final.loc[confirmados, "Quant."] = df_final.loc[confirmados].groupby(
                ["Voo", col_agrupamento]
            )["Missionários"].transform("count")
            df_final.loc[confirmados, "Transportes"] = df_final.loc[confirmados, "Quant."].apply(
                lambda q: definir_transporte(q, com_mala=True)
            )

        df_final = aplicar_design(df_final, modo)
        
        st.session_state['resultado'] = df_final
        st.session_state['modo'] = modo

# --- EXIBIÇÃO ---
if 'resultado' in st.session_state:
    df = st.session_state['resultado']
    st.subheader(f"{st.session_state['modo']} - modo de visualização")
    
    if "Transportes" in df.columns:
        van = len(df[df["Transportes"].str.contains("VAN", na=False, case=False)])
        onibus = len(df[df["Transportes"].str.contains("ÔNIBUS", na=False, case=False)])
        carro = len(df[df["Transportes"].str.contains("CARRO", na=False, case=False)])
        pendentes = len(df[df["Status do Voo"] == "Pendente de voo"])
        
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Missionários", len(df))
        c2.metric("Carros Requeridos", carro)
        c3.metric("Vans Requeridas", van)
        c4.metric("Ônibus Requeridos", onibus)
        c5.metric("Voos Pendentes", pendentes)
    
    st.dataframe(df, use_container_width=True, height=450)
    
    saida = PASTA_BASE / f"{st.session_state['modo']}_Final_Logistica.xlsx"
    if st.button("Exportar Planilha Oficial (Formatada)", type="primary"):
        from modelos import aplicar_cores_e_salvar
        aplicar_cores_e_salvar(df, saida, st.session_state['modo'])
        st.success(f"Arquivo salvo com sucesso!")