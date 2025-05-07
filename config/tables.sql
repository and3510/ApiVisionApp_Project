-- Banco de Dados CIN


-- Tabela: identidade
CREATE TABLE identidade (
    cpf VARCHAR(14) PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    nome_mae VARCHAR(150) NOT NULL,
    nome_pai VARCHAR(150) NOT NULL,
    data_nascimento VARCHAR(20) NOT NULL,
    vetor_facial VECTOR(128) NOT NULL,
    url_facial VARCHAR(200) NOT NULL,

);



-- Tabela: usuario
CREATE TABLE usuario (
    matricula VARCHAR(10) PRIMARY KEY,
    id_usuario VARCHAR(100),
    nome VARCHAR(150),
    nome_social VARCHAR(150),
    nome_mae VARCHAR(150),
    nome_pai VARCHAR(150),
    data_nascimento VARCHAR(20),
    cpf VARCHAR(14) unique REFERENCES identidade(cpf),
    telefone VARCHAR(20),
    sexo CHAR(5),  -- Ex: 'M', 'F', 'O'
    nacionalidade VARCHAR(100),
    naturalidade VARCHAR(100),
    tipo_sanguineo VARCHAR(5),
    cargo VARCHAR(100),
    nivel_classe VARCHAR(50),
    senha TEXT,
    data_criacao_conta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Banco de Dados SSP


-- Tabela: pessoa_alerta
CREATE TABLE pessoa_alerta (
    id_alerta VARCHAR(30) PRIMARY KEY DEFAULT gen_random_uuid(),
    cpf VARCHAR(14) REFERENCES identidade(cpf),
    matricula VARCHAR(10) REFERENCES usuario(matricula)
);


-- Tabela: mensagem_alerta
CREATE TABLE mensagem_alerta (
    id_alerta VARCHAR REFERENCES pessoa_alerta(id_alerta),
    id_mensagem VARCHAR(30) PRIMARY KEY DEFAULT gen_random_uuid(),
    data_mensagem VARCHAR(50),
    conteudo_mensagem TEXT,
    matricula VARCHAR(10) REFERENCES usuario(matricula),
    localizacao VARCHAR(150),
    cpf VARCHAR(14) REFERENCES identidade(cpf)
);


-- Tabela: ficha_criminal
CREATE TABLE ficha_criminal (
    id_ficha VARCHAR(30) PRIMARY KEY DEFAULT gen_random_uuid(),
    cpf VARCHAR(14) REFERENCES identidade(cpf),
    vulgo VARCHAR(100),
    foragido BOOLEAN
);

-- Tabela: crime
CREATE TABLE crime (
    id_crime VARCHAR(30) PRIMARY KEY DEFAULT gen_random_uuid(),
    id_ficha VARCHAR REFERENCES ficha_criminal(id_ficha),
    nome_crime VARCHAR(150),
    artigo VARCHAR(50),
    descricao TEXT,
    data_ocorrencia VARCHAR(20),
    cidade VARCHAR(100),
    estado CHAR(2),
    status VARCHAR(20) CHECK (status IN ('Em Aberto', 'Condenado', 'Absolvido', 'Arquivado', 'Cumprido')),
);

