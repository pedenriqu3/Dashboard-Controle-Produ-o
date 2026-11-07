import os 
from decimal import Decimal
import mysql.connector
import pandas as pd
import streamlit as st 
from mysql.connector import Error

st.set_page_config(page_title="AF Sacolas", page_icon="🛍️", layout="wide")

STATUS_OPCOES = ["Criado", "Em produção", "Enviado", "Entregue", "Cancelado"]
PAGAMENTO_OPCOES = ["Cartão de crédito", "Boleto", "Pix", "Transferência"]


# Conexão e helpers de banco
def get_conn():
    """Abre uma conexão nova usando os dados preenchidos na barra lateral."""
    return mysql.connector.connect(
        host=st.session_state["db_host"],
        port=int(st.session_state["db_port"]),
        user=st.session_state["db_user"],
        password=st.session_state["db_password"],
        database=st.session_state["db_name"],
    )


def consultar(sql, params=None) -> pd.DataFrame:
    """SELECT -> DataFrame (Decimal vira float para formatar/plotar)."""
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        df = pd.DataFrame(cur.fetchall())
    finally:
        conn.close()
    for col in df.columns:
        if df[col].map(lambda x: isinstance(x, Decimal)).any():
            df[col] = df[col].astype(float)
    return df


def brl(valor) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def flash(msg, tipo="success"):
    st.session_state["flash"] = (tipo, msg)


# Operações (scripts SQL executados pelos botões)
def inserir_pedido(id_cliente, status, pagamento, itens) -> int:
    """Insere pedido + itens e recalcula valor_total, tudo em uma transação."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Pedidos (id_cliente, status_pedido, forma_pagamento) "
            "VALUES (%s, %s, %s)",
            (id_cliente, status, pagamento),
        )
        id_pedido = cur.lastrowid
        cur.executemany(
            "INSERT INTO Itens_Pedido "
            "(id_pedido, id_produto, quantidade, preco_unitario, cor_personalizada) "
            "VALUES (%s, %s, %s, %s, %s)",
            [
                (id_pedido, i["id_produto"], i["quantidade"], i["preco_unitario"], i["cor"])
                for i in itens
            ],
        )
        cur.execute(
            "UPDATE Pedidos SET valor_total = ("
            "  SELECT SUM(quantidade * preco_unitario) FROM Itens_Pedido WHERE id_pedido = %s"
            ") WHERE id_pedido = %s",
            (id_pedido, id_pedido),
        )
        conn.commit()
        return id_pedido
    except Error:
        conn.rollback()
        raise
    finally:
        conn.close()


def deletar_pedido(id_pedido):
    """Apaga os itens (FK) e depois o pedido, em uma transação."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM Itens_Pedido WHERE id_pedido = %s", (id_pedido,))
        cur.execute("DELETE FROM Pedidos WHERE id_pedido = %s", (id_pedido,))
        conn.commit()
    except Error:
        conn.rollback()
        raise
    finally:
        conn.close()


def atualizar_status(id_pedido, status):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE Pedidos SET status_pedido = %s WHERE id_pedido = %s",
            (status, id_pedido),
        )
        conn.commit()
    except Error:
        conn.rollback()
        raise
    finally:
        conn.close()


# Barra lateral: conexão e navegação
def sidebar() -> str:
    st.sidebar.title("🛍️ AF Sacolas")
    pagina = st.sidebar.radio(
        "Navegação", ["📊 Dashboard", "📋 Pedidos", "➕ Novo pedido"]
    )
    with st.sidebar.expander("⚙️ Conexão com o MySQL"):
        st.text_input("Host", os.getenv("DB_HOST", "localhost"), key="db_host")
        st.text_input("Porta", os.getenv("DB_PORT", "3306"), key="db_port")
        st.text_input("Usuário", os.getenv("DB_USER", "root"), key="db_user")
        st.text_input("Senha", os.getenv("DB_PASSWORD", ""), type="password", key="db_password")
        st.text_input("Banco", os.getenv("DB_NAME", "schema2_af_sacolas"), key="db_name")
    return pagina


# Páginas
def pagina_dashboard():
    st.header("📊 Visão geral")

    resumo = consultar(
        "SELECT COUNT(*) AS pedidos, COALESCE(SUM(valor_total), 0) AS faturamento FROM Pedidos"
    ).iloc[0]
    pedidos = int(resumo["pedidos"])
    faturamento = float(resumo["faturamento"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Pedidos", pedidos)
    c2.metric("Faturamento", brl(faturamento))
    c3.metric("Ticket médio", brl(faturamento / pedidos) if pedidos else brl(0))

    st.subheader("Faturamento por estado")
    por_uf = consultar("SELECT * FROM vw_faturamento_por_estado")
    if por_uf.empty:
        st.info("Ainda não há pedidos.")
    else:
        col_a, col_b = st.columns(2)
        col_a.dataframe(
            por_uf,
            hide_index=True,
            use_container_width=True,
            column_config={
                "uf": "UF",
                "total_pedidos": "Pedidos",
                "faturamento_total": st.column_config.NumberColumn("Faturamento", format="R$ %.2f"),
            },
        )
        col_b.bar_chart(por_uf.set_index("uf")["faturamento_total"])

    st.subheader("Pedidos por status")
    status = consultar(
        "SELECT status_pedido AS status, COUNT(*) AS total FROM Pedidos GROUP BY status_pedido"
    )
    if not status.empty:
        st.bar_chart(status.set_index("status")["total"])


def pagina_pedidos():
    st.header("📋 Pedidos")

    pedidos = consultar(
        "SELECT p.id_pedido, c.nome_razao_social AS cliente, c.uf, p.data_pedido, "
        "p.status_pedido AS status, p.forma_pagamento AS pagamento, p.valor_total "
        "FROM Pedidos p INNER JOIN Clientes c ON c.id_cliente = p.id_cliente "
        "ORDER BY p.id_pedido DESC"
    )
    if pedidos.empty:
        st.info("Nenhum pedido cadastrado. Use **➕ Novo pedido**.")
        return

    filtro = st.multiselect("Filtrar por status", sorted(pedidos["status"].dropna().unique()))
    visiveis = pedidos[pedidos["status"].isin(filtro)] if filtro else pedidos
    st.dataframe(
        visiveis,
        hide_index=True,
        use_container_width=True,
        column_config={
            "id_pedido": "Nº",
            "data_pedido": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm"),
            "valor_total": st.column_config.NumberColumn("Total", format="R$ %.2f"),
        },
    )

    st.divider()
    ids = visiveis["id_pedido"].tolist()
    if not ids:
        return
    escolhido = st.selectbox("Selecione um pedido", ids, format_func=lambda i: f"Pedido #{i}")

    st.subheader(f"Itens do pedido #{escolhido}")
    itens = consultar(
        "SELECT nome_modelo, quantidade, preco_unitario, subtotal_item "
        "FROM vw_detalhes_pedidos WHERE id_pedido = %s",
        (escolhido,),
    )
    st.dataframe(
        itens,
        hide_index=True,
        use_container_width=True,
        column_config={
            "nome_modelo": "Produto",
            "quantidade": "Qtd",
            "preco_unitario": st.column_config.NumberColumn("Preço unit.", format="R$ %.2f"),
            "subtotal_item": st.column_config.NumberColumn("Subtotal", format="R$ %.2f"),
        },
    )

    col_status, col_del = st.columns(2)
    with col_status:
        st.markdown("**Atualizar status**")
        atual = visiveis.loc[visiveis["id_pedido"] == escolhido, "status"].iloc[0]
        opcoes = STATUS_OPCOES if atual in STATUS_OPCOES else [atual] + STATUS_OPCOES
        novo = st.selectbox("Novo status", opcoes, index=opcoes.index(atual), key="novo_status")
        if st.button("Salvar status"):
            try:
                atualizar_status(escolhido, novo)
                flash(f"Status do pedido #{escolhido} atualizado para '{novo}'.")
                st.rerun()
            except Error as e:
                st.error(f"Erro ao atualizar: {e}")
    with col_del:
        st.markdown("**Deletar pedido**")
        confirma = st.checkbox(f"Confirmo a exclusão do pedido #{escolhido}", key="confirma_del")
        if st.button("🗑️ Deletar", type="primary", disabled=not confirma):
            try:
                deletar_pedido(escolhido)
                flash(f"Pedido #{escolhido} deletado.")
                st.session_state["confirma_del"] = False
                st.rerun()
            except Error as e:
                st.error(f"Erro ao deletar: {e}")


def pagina_novo_pedido():
    st.header("➕ Novo pedido")
    carrinho = st.session_state.setdefault("carrinho", [])

    clientes = consultar(
        "SELECT id_cliente, nome_razao_social, cidade, uf FROM Clientes ORDER BY nome_razao_social"
    )
    produtos = consultar(
        "SELECT id_produto, nome_modelo, material, dimensoes, preco_base FROM Produtos ORDER BY nome_modelo"
    )
    if clientes.empty or produtos.empty:
        st.warning("Cadastre ao menos um cliente e um produto antes de criar pedidos.")
        return

    st.subheader("1. Dados do pedido")
    c1, c2, c3 = st.columns(3)
    cliente_id = c1.selectbox(
        "Cliente",
        clientes["id_cliente"].tolist(),
        format_func=lambda i: clientes.loc[clientes["id_cliente"] == i, "nome_razao_social"].iloc[0],
    )
    status = c2.selectbox("Status", STATUS_OPCOES)
    pagamento = c3.selectbox("Forma de pagamento", PAGAMENTO_OPCOES)

    st.subheader("2. Itens")
    prod_id = st.selectbox(
        "Produto",
        produtos["id_produto"].tolist(),
        format_func=lambda i: (
            lambda r: f"{r.nome_modelo} - {r.dimensoes} ({brl(r.preco_base)})"
        )(produtos.loc[produtos["id_produto"] == i].iloc[0]),
    )
    preco_base = float(produtos.loc[produtos["id_produto"] == prod_id, "preco_base"].iloc[0])
    i1, i2, i3 = st.columns(3)
    qtd = i1.number_input("Quantidade", min_value=1, value=100, step=50)
    preco = i2.number_input(
        "Preço unitário (R$)", min_value=0.01, value=preco_base, step=0.10, format="%.2f",
        key=f"preco_{prod_id}",
    )
    cor = i3.text_input("Cor / personalização")
    if st.button("Adicionar item"):
        carrinho.append(
            {
                "id_produto": int(prod_id),
                "produto": produtos.loc[produtos["id_produto"] == prod_id, "nome_modelo"].iloc[0],
                "quantidade": int(qtd),
                "preco_unitario": round(float(preco), 2),
                "cor": cor.strip() or None,
            }
        )
        st.rerun()

    if carrinho:
        df = pd.DataFrame(carrinho)
        df["subtotal"] = df["quantidade"] * df["preco_unitario"]
        st.dataframe(
            df.drop(columns=["id_produto"]),
            hide_index=True,
            use_container_width=True,
            column_config={
                "produto": "Produto",
                "quantidade": "Qtd",
                "preco_unitario": st.column_config.NumberColumn("Preço unit.", format="R$ %.2f"),
                "cor": "Cor / personalização",
                "subtotal": st.column_config.NumberColumn("Subtotal", format="R$ %.2f"),
            },
        )
        st.metric("Total do pedido", brl(df["subtotal"].sum()))

        b1, b2, _ = st.columns([1, 1, 3])
        if b1.button("Remover último"):
            carrinho.pop()
            st.rerun()
        if b2.button("💾 Salvar pedido", type="primary"):
            try:
                novo_id = inserir_pedido(int(cliente_id), status, pagamento, carrinho)
                st.session_state["carrinho"] = []
                flash(f"Pedido #{novo_id} criado com sucesso.")
                st.rerun()
            except Error as e:
                st.error(f"Erro ao salvar: {e}")
    else:
        st.caption("Nenhum item adicionado ainda.")


# Main
pagina = sidebar()

if "flash" in st.session_state:
    tipo, msg = st.session_state.pop("flash")
    (st.success if tipo == "success" else st.error)(msg)

try:
    {
        "📊 Dashboard": pagina_dashboard,
        "📋 Pedidos": pagina_pedidos,
        "➕ Novo pedido": pagina_novo_pedido,
    }[pagina]()
except Error as e:
    st.error(
        f"Não foi possível acessar o banco: {e}\n\n"
        "Verifique se o MySQL está rodando, se o script `TrabalhoSegundaUnidade.sql` "
        "já foi executado e se os dados da barra lateral (⚙️ Conexão) estão corretos."
    )
