-- Cria o banco de dados específico para o nosso backend (Esse if so roda se não existir o banco de dados ainda)
CREATE DATABASE IF NOT EXISTS schema2_af_sacolas;

-- Informa ao MySQL que vamos usar este banco a partir de agora
USE schema2_af_sacolas;

-- Tabela 1: Clientes
CREATE TABLE Clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY, -- Toda vez que inserir um cliente novo, ele vai somar um automaticamente
    nome_razao_social VARCHAR(100) NOT NULL,
    cnpj_cpf VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100),
    telefone VARCHAR(20),
    cidade VARCHAR(50),
    uf CHAR(2) NOT NULL 
);

-- Tabela 2: Produtos
CREATE TABLE Produtos (
    id_produto INT AUTO_INCREMENT PRIMARY KEY,
    nome_modelo VARCHAR(100) NOT NULL,
    material VARCHAR(50),
    dimensoes VARCHAR(50),
    preco_base DECIMAL(10, 2) NOT NULL, -- DECIMAL para armazenar centavos, os últimos dois digitos 
    estoque_minimo INT DEFAULT 0 -- O "DEFAULT 0" significa que se não informarmos nada, ele assume zero.
);

-- Tabela 3: Pedidos
CREATE TABLE Pedidos (
    id_pedido INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL, -- Chave Estranteira
    data_pedido DATETIME DEFAULT CURRENT_TIMESTAMP, -- Salva automaticamente o dia e a hora da compra, se não colocar nada vai ser a data atual
    status_pedido VARCHAR(50) DEFAULT 'Criado',
    forma_pagamento VARCHAR(50),
    valor_total DECIMAL(10, 2) DEFAULT 0.00,
    
    -- Aqui criamos a Restrição de Integridade Referencial (Chave Estrangeira)
    FOREIGN KEY (id_cliente) REFERENCES Clientes(id_cliente)
);

-- Tabela 4: Itens do Pedido (Tabela associativa entre Pedido e Produto)
CREATE TABLE Itens_Pedido (
    id_item INT AUTO_INCREMENT PRIMARY KEY,
    id_pedido INT NOT NULL, -- Chave Estrangeira ligando ao Pedido
    id_produto INT NOT NULL, -- Chave Estrangeira ligando ao Produto
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10, 2) NOT NULL, -- Salvamos o preço aqui caso o preço base do produto mude no futuro
    cor_personalizada VARCHAR(50),
    
    FOREIGN KEY (id_pedido) REFERENCES Pedidos(id_pedido),
    FOREIGN KEY (id_produto) REFERENCES Produtos(id_produto)
);

-- Inserindo Clientes
INSERT INTO Clientes (nome_razao_social, cnpj_cpf, email, telefone, cidade, uf) VALUES
('Boutique Moda SP', '11.111.111/0001-11', 'contato@modasp.com', '11999998888', 'São Paulo', 'SP'),
('Artesanatos Potiguar', '22.222.222/0001-22', 'vendas@artespotiguar.com', '84988887777', 'Natal', 'RN'),
('Doceria Paraibana', '33.333.333/0001-33', 'pedidos@doceriapb.com', '83977776666', 'João Pessoa', 'PB');

-- Inserindo Produtos
INSERT INTO Produtos (nome_modelo, material, dimensoes, preco_base, estoque_minimo) VALUES
('Sacola Kraft G', 'Papel Kraft', '30x40x15cm', 2.50, 500),
('Sacola Kraft M', 'Papel Kraft', '20x30x10cm', 1.80, 500),
('Sacola Boutique P', 'Papel Couchê Brilho', '15x20x8cm', 4.50, 200),
('Sacola Ecológica TNT', 'Tecido TNT', '40x40x20cm', 3.00, 300);

-- Inserindo Pedidos
INSERT INTO Pedidos (id_cliente, status_pedido, forma_pagamento) VALUES
(1, 'Entregue', 'Cartão de crédito'), 
(2, 'Enviado', 'Boleto'), 
(3, 'Criado', 'Cartão de crédito');

-- Inserindo Itens dos Pedidos
INSERT INTO Itens_Pedido (id_pedido, id_produto, quantidade, preco_unitario, cor_personalizada) VALUES
(1, 3, 1000, 4.20, 'Preto com logo Dourada'), 
(2, 1, 500, 2.50, 'Impressão Preta Simples'), 
(2, 2, 500, 1.80, 'Impressão Preta Simples'), 
(3, 4, 300, 3.00, 'Vermelho com logo Branca');

-- Atualizando os valores totais dos Pedidos
UPDATE Pedidos SET valor_total = 4200.00 WHERE id_pedido = 1;
UPDATE Pedidos SET valor_total = 2150.00 WHERE id_pedido = 2;
UPDATE Pedidos SET valor_total = 900.00 WHERE id_pedido = 3;

-- View 1: Detalhamento Completo dos Pedidos (Une as 4 tabelas em uma visão só)
CREATE VIEW vw_detalhes_pedidos AS
SELECT 
    p.id_pedido,
    c.nome_razao_social,
    c.uf,
    pr.nome_modelo,
    i.quantidade,
    i.preco_unitario,
    (i.quantidade * i.preco_unitario) AS subtotal_item,
    p.status_pedido
FROM Pedidos p
INNER JOIN Clientes c ON p.id_cliente = c.id_cliente
INNER JOIN Itens_Pedido i ON p.id_pedido = i.id_pedido
INNER JOIN Produtos pr ON i.id_produto = pr.id_produto;

-- View 2: Faturamento e Pedidos por Estado (Relacionado com o Schema 1)
CREATE VIEW vw_faturamento_por_estado AS
SELECT 
    c.uf,
    COUNT(DISTINCT p.id_pedido) AS total_pedidos,
    SUM(p.valor_total) AS faturamento_total
FROM Clientes c
INNER JOIN Pedidos p ON c.id_cliente = p.id_cliente
GROUP BY c.uf
ORDER BY faturamento_total DESC;