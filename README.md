# AF Sacolas

Aplicação web para acompanhamento de pedidos de uma empresa de sacolas personalizadas. O projeto integra um banco de dados MySQL a um dashboard desenvolvido com Streamlit.

## Funcionalidades

- Visualização de indicadores gerais:
  - quantidade de pedidos;
  - faturamento total;
  - ticket médio;
  - faturamento por estado;
  - pedidos por status.
- Consulta e filtro de pedidos por status.
- Visualização dos itens de cada pedido.
- Atualização do status de um pedido.
- Exclusão de pedidos.
- Cadastro de novos pedidos com um ou mais itens, quantidade, preço unitário e personalização.
- Cálculo automático do total do pedido.

## Tecnologias

- Python 3.10 ou superior
- Streamlit
- Pandas
- MySQL
- MySQL Connector/Python

## Estrutura do projeto

```text
.
├── dashboard/
│   ├── app.py
│   └── requirements.txt
├── Diagrama.pdf
├── Diagrama.png
├── TrabalhoSegundaUnidade.sql
└── README.md
```

## Pré-requisitos

Antes de executar a aplicação, instale:

1. [Python](https://www.python.org/downloads/)
2. [MySQL Server](https://dev.mysql.com/downloads/mysql/)
3. `pip`, normalmente instalado junto com o Python

## Configuração do banco de dados

1. Inicie o servidor MySQL.
2. Execute o script [`TrabalhoSegundaUnidade.sql`](./TrabalhoSegundaUnidade.sql) em um cliente MySQL, como o MySQL Workbench ou o terminal:

   ```bash
   mysql -u root -p < TrabalhoSegundaUnidade.sql
   ```

O script cria o banco `schema2_af_sacolas`, as tabelas, os dados iniciais e as views utilizadas pelo dashboard.

## Instalação

Na raiz do projeto, crie e ative um ambiente virtual:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r dashboard/requirements.txt
```

## Execução

Com o ambiente virtual ativado, execute:

```bash
streamlit run dashboard/app.py
```

O Streamlit abrirá a aplicação no navegador, normalmente em [http://localhost:8501](http://localhost:8501).

Na barra lateral, abra **Conexão com o MySQL** e informe:

| Campo | Valor padrão |
|---|---|
| Host | `localhost` |
| Porta | `3306` |
| Usuário | `root` |
| Senha | senha configurada no MySQL |
| Banco | `schema2_af_sacolas` |

Também é possível definir os valores por variáveis de ambiente antes de iniciar a aplicação:

```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "3306"
$env:DB_USER = "root"
$env:DB_PASSWORD = "sua_senha"
$env:DB_NAME = "schema2_af_sacolas"
streamlit run dashboard/app.py
```

## Modelo de dados

O banco possui as principais entidades:

- `Clientes`: dados dos clientes;
- `Produtos`: modelos de sacolas e preços base;
- `Pedidos`: informações gerais dos pedidos;
- `Itens_Pedido`: produtos e quantidades de cada pedido.

As views utilizadas pela aplicação são:

- `vw_detalhes_pedidos`: detalhamento dos itens dos pedidos;
- `vw_faturamento_por_estado`: consolidação de pedidos e faturamento por UF.

O diagrama do banco está disponível em [`Diagrama.png`](./Diagrama.png) e [`Diagrama.pdf`](./Diagrama.pdf).

## Fluxo de uso

1. Configure o banco executando o script SQL.
2. Inicie o dashboard.
3. Confirme os dados de conexão na barra lateral.
4. Consulte os indicadores na página **Dashboard**.
5. Gerencie pedidos na página **Pedidos**.
6. Crie pedidos na página **Novo pedido**.

## Observações

- O banco precisa estar em execução para o dashboard consultar ou alterar dados.
- O script SQL contém dados iniciais para facilitar a demonstração.
- A senha do MySQL não é armazenada no código; ela é informada pela barra lateral ou por variável de ambiente.
