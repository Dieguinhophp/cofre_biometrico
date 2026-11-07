CREATE DATABASE IF NOT EXISTS cofre_biometrico CHARACTER SET utf8mb4;
USE cofre_biometrico;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    nivel TINYINT NOT NULL,           -- 1 = geral, 2 = diretor, 3 = ministro
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Vários vetores (embeddings de 128 dimensões) por usuário
CREATE TABLE IF NOT EXISTS encodings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    vetor TEXT NOT NULL,              -- lista JSON com 128 floats
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS logs_acesso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NULL,
    nome_detectado VARCHAR(100),
    nivel_exigido TINYINT NOT NULL,
    resultado ENUM('CONCEDIDO','NEGADO') NOT NULL,
    motivo VARCHAR(200),
    distancia FLOAT NULL,
    data_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);
