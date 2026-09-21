import streamlit as st
import sqlite3
import json
from datetime import datetime

# Configuracao da pagina
st.set_page_config(
    page_title="Organizador de Ativos",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS customizado (mobile-first)
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .stButton>button { width: 100%; border-radius: 8px; }
    .ticker-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        margin: 3px;
        border: 1px solid rgba(128,128,128,0.3);
        background: rgba(128,128,128,0.08);
    }
    .category-card {
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        background: rgba(128,128,128,0.03);
    }
    .dot {
        width: 10px; height: 10px; border-radius: 50%;
        display: inline-block; margin-right: 8px;
    }
    h3 { margin-bottom: 4px !important; margin-top: 0 !important; }
    .small { font-size: 12px; color: #888; }
</style>
""", unsafe_allow_html=True)

# Banco de dados SQLite
DB_PATH = "ativos.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            cor TEXT DEFAULT "#1f77b4",
            criado_em TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS tickers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            adicionado_em TEXT,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def get_categorias():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, nome, cor FROM categorias ORDER BY nome")
    cats = c.fetchall()
    conn.close()
    return cats

def add_categoria(nome, cor):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO categorias (nome, cor, criado_em) VALUES (?, ?, ?)",
                  (nome.upper(), cor, datetime.now().isoformat()))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def del_categoria(cat_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM categorias WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()

def get_tickers(cat_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, ticker FROM tickers WHERE categoria_id = ? ORDER BY ticker", (cat_id,))
    items = c.fetchall()
    conn.close()
    return items

def add_ticker(cat_id, ticker):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM tickers WHERE categoria_id = ? AND ticker = ?", (cat_id, ticker.upper()))
    if not c.fetchone():
        c.execute("INSERT INTO tickers (categoria_id, ticker, adicionado_em) VALUES (?, ?, ?)",
                  (cat_id, ticker.upper(), datetime.now().isoformat()))
        conn.commit()
    conn.close()

def del_ticker(ticker_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM tickers WHERE id = ?", (ticker_id,))
    conn.commit()
    conn.close()

def exportar_json():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, nome, cor FROM categorias")
    cats = c.fetchall()
    data = []
    for cid, nome, cor in cats:
        c.execute("SELECT ticker FROM tickers WHERE categoria_id = ?", (cid,))
        tickers = [r[0] for r in c.fetchall()]
        data.append({"nome": nome, "cor": cor, "tickers": tickers})
    conn.close()
    return json.dumps(data, indent=2, ensure_ascii=False)

def importar_json(raw):
    data = json.loads(raw)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for item in data:
        nome = item.get("nome", "").upper()
        cor = item.get("cor", "#1f77b4")
        tickers = item.get("tickers", [])
        if not nome:
            continue
        c.execute("INSERT OR IGNORE INTO categorias (nome, cor, criado_em) VALUES (?, ?, ?)",
                  (nome, cor, datetime.now().isoformat()))
        c.execute("SELECT id FROM categorias WHERE nome = ?", (nome,))
        row = c.fetchone()
        if row:
            cat_id = row[0]
            for t in tickers:
                c.execute("INSERT OR IGNORE INTO tickers (categoria_id, ticker, adicionado_em) VALUES (?, ?, ?)",
                          (cat_id, t.upper(), datetime.now().isoformat()))
    conn.commit()
    conn.close()

# Cores disponiveis
CORES = {
    "Azul": "#1f77b4",
    "Vermelho": "#d62728",
    "Verde": "#2ca02c",
    "Roxo": "#9467bd",
    "Laranja": "#ff7f0e",
    "Cinza": "#7f7f7f",
    "Rosa": "#e377c2",
    "Marrom": "#8c564b",
}

# Inicializacao
init_db()

# Header
st.title("📊 Organizador de Ativos")
st.caption("Crie categorias e agrupe seus tickers. Acesse de qualquer lugar.")

# Abas
tab1, tab2 = st.tabs(["🗂️ Minhas Categorias", "⚙️ Backup / Restaurar"])

with tab1:
    # Nova categoria
    with st.expander("➕ Nova categoria", expanded=False):
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            novo_nome = st.text_input("Nome da categoria", placeholder="Ex: Commodities", key="novo_nome")
        with col2:
            nova_cor = st.selectbox("Cor", list(CORES.keys()), key="nova_cor")
        with col3:
            st.write("")
            st.write("")
            if st.button("Adicionar", use_container_width=True):
                if novo_nome.strip():
                    add_categoria(novo_nome.strip(), CORES[nova_cor])
                    st.success(f"Categoria '{novo_nome.strip().upper()}' criada!")
                    st.rerun()
                else:
                    st.warning("Digite um nome.")

    # Listar categorias
    categorias = get_categorias()
    if not categorias:
        st.info("Nenhuma categoria ainda. Crie a primeira acima ☝️")
    else:
        for cat_id, nome, cor in categorias:
            with st.container():
                st.markdown('<div class="category-card">', unsafe_allow_html=True)

                # Header da categoria
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f'<h3><span class="dot" style="background:{cor}"></span>{nome}</h3>', unsafe_allow_html=True)
                with c2:
                    if st.button("🗑️", key=f"del_cat_{cat_id}", help="Remover categoria"):
                        del_categoria(cat_id)
                        st.rerun()

                # Tickers
                tickers = get_tickers(cat_id)
                if tickers:
                    cols = st.columns(4)
                    for idx, (tid, ticker) in enumerate(tickers):
                        with cols[idx % 4]:
                            if st.button(f"❌ {ticker}", key=f"del_ticker_{tid}", help="Remover ticker"):
                                del_ticker(tid)
                                st.rerun()
                else:
                    st.markdown('<span class="small">Nenhum ativo nesta categoria.</span>', unsafe_allow_html=True)

                # Adicionar ticker
                novo_ticker = st.text_input(f"Adicionar ticker em {nome}", placeholder="Ex: PETR4", key=f"ticker_input_{cat_id}")
                if novo_ticker.strip():
                    add_ticker(cat_id, novo_ticker.strip())
                    st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.subheader("📤 Exportar dados")
    dados = exportar_json()
    st.download_button(
        label="Baixar JSON",
        data=dados,
        file_name="organizador_ativos.json",
        mime="application/json",
        use_container_width=True
    )

    st.subheader("📥 Importar dados")
    uploaded = st.file_uploader("Selecione um arquivo JSON", type=["json"])
    if uploaded is not None:
        try:
            content = uploaded.read().decode("utf-8")
            importar_json(content)
            st.success("Dados importados com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao importar: {e}")

    st.subheader("🧹 Limpar tudo")
    if st.button("Apagar todas as categorias e tickers", use_container_width=True):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM tickers")
        c.execute("DELETE FROM categorias")
        conn.commit()
        conn.close()
        st.success("Banco de dados limpo.")
        st.rerun()

# Footer
st.divider()
st.caption("💡 Dica: adicione tickers como PETR4, VALE3, ITUB4, etc. Os dados ficam salvos automaticamente.")