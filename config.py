"""Configurações gerais do sistema de acesso biométrico ao cofre."""

# Banco de dados (XAMPP padrão: usuário root, sem senha)
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "cofre_biometrico",
}

# Câmera
CAMERA_INDEX = 0

# Níveis de segurança
NIVEIS = {
    1: "Nível 1 - Permissão geral",
    2: "Nível 2 - Diretor de divisão",
    3: "Nível 3 - Ministro do Meio Ambiente",
}

# Reconhecimento
LIMIAR_DISTANCIA = 0.50     # menor = mais rigoroso (0.6 é o padrão da biblioteca)
NUM_FOTOS_CADASTRO = 5      # capturas por usuário
ESCALA_DETECCAO = 0.5       # reduz a imagem para detectar mais rápido
BRILHO_MINIMO = 60          # 0-255; abaixo disso a iluminação é insuficiente

# Detecção de vivacidade (anti-foto) por piscada
EAR_LIMIAR = 0.21           # olho fechado quando EAR < limiar
EAR_FRAMES_FECHADO = 2      # frames seguidos com olho fechado para contar piscada
PISCADAS_NECESSARIAS = 1
TEMPO_LIMITE_SEGUNDOS = 15  # tempo máximo para concluir a autenticação

# Painel administrativo (simulação de segurança adicional)
ADMIN_USUARIO = "admin"
# SHA-256 da senha "123" (a senha não fica em texto puro no código)
ADMIN_SENHA_HASH = "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"

# Tempo máximo (segundos) com o cofre aberto antes de encerrar a sessão
SESSAO_COFRE_SEGUNDOS = 90
