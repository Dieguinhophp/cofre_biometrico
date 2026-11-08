"""Conteúdo FICTÍCIO dos cofres (apenas para fins acadêmicos/demonstração).

Todos os nomes, códigos, locais e números abaixo são inventados.
"""

COFRES = {
    1: {
        "nome": "Cofre Geral",
        "perfil": "Permissão geral",
        "descricao": "Documentos operacionais e protocolos de uso comum dos servidores "
                     "do Ministério do Meio Ambiente.",
        "documentos": [
            {
                "codigo": "G-001",
                "titulo": "Manual de Biossegurança Básica",
                "classificacao": "Uso interno",
                "data": "12/03/2026",
                "autor": "Coordenação de Segurança Ambiental",
                "corpo": (
                    "Este manual reúne as regras mínimas de conduta para quem circula em "
                    "áreas de armazenamento do Ministério.\n\n"
                    "1. Identificação: crachá visível em todas as áreas controladas.\n"
                    "2. Equipamentos: luvas, óculos e jaleco obrigatórios nos laboratórios.\n"
                    "3. Comunicação: qualquer incidente deve ser registrado em até 1 hora "
                    "no sistema de ocorrências.\n"
                    "4. Visitantes: sempre acompanhados por um servidor credenciado.\n\n"
                    "Em caso de dúvida, contate a Coordenação de Segurança Ambiental."
                ),
            },
            {
                "codigo": "G-002",
                "titulo": "Calendário de Inspeções Ambientais 2026",
                "classificacao": "Uso interno",
                "data": "05/01/2026",
                "autor": "Diretoria de Fiscalização",
                "corpo": (
                    "Cronograma anual de inspeções (fictício):\n\n"
                    "  • Janeiro   - Bacia do Rio Verde (qualidade da água)\n"
                    "  • Março     - Polo industrial de Vale Azul\n"
                    "  • Maio      - Reserva Serra Dourada (fauna)\n"
                    "  • Agosto    - Aterros regionais da Região Sul\n"
                    "  • Outubro   - Estuário de Porto Claro\n\n"
                    "As equipes são definidas trimestralmente pela Diretoria."
                ),
            },
            {
                "codigo": "G-003",
                "titulo": "Lista de Laboratórios Credenciados",
                "classificacao": "Público interno",
                "data": "20/02/2026",
                "autor": "Secretaria de Pesquisa",
                "corpo": (
                    "Laboratórios aptos a emitir laudos para o Ministério (fictícios):\n\n"
                    "  LAB-01  Instituto Aquário de Análises ........ Região Norte\n"
                    "  LAB-02  Centro de Ecotoxicologia Vale Azul ... Região Sudeste\n"
                    "  LAB-03  Laboratório Federal Serra Dourada .... Região Centro-Oeste\n"
                    "  LAB-04  Núcleo de Monitoramento Porto Claro .. Região Sul\n\n"
                    "Renovação de credenciamento a cada 24 meses."
                ),
            },
            {
                "codigo": "G-004",
                "titulo": "Protocolo de Descarte de Resíduos Comuns",
                "classificacao": "Uso interno",
                "data": "30/04/2026",
                "autor": "Divisão de Resíduos",
                "corpo": (
                    "Fluxo padrão para resíduos de baixo risco:\n\n"
                    "  1. Separar por categoria (papel, plástico, orgânico, eletrônico).\n"
                    "  2. Identificar o recipiente com etiqueta e data.\n"
                    "  3. Encaminhar à central de coleta até as 16h.\n"
                    "  4. Registrar a retirada no sistema.\n\n"
                    "Resíduos de risco elevado seguem protocolos de nível superior."
                ),
            },
        ],
    },
    2: {
        "nome": "Cofre Restrito",
        "perfil": "Diretores de divisão",
        "descricao": "Inventários, auditorias e planos de contingência das divisões. "
                     "Acesso restrito a diretores e ao ministro.",
        "documentos": [
            {
                "codigo": "D-101",
                "titulo": "Inventário de Substâncias Controladas - Divisão Sul",
                "classificacao": "Restrito",
                "data": "18/06/2026",
                "autor": "Diretoria da Divisão Sul",
                "corpo": (
                    "Inventário fictício de substâncias sob controle (códigos inventados):\n\n"
                    "  CÓDIGO     QUANTIDADE   LOCAL           SITUAÇÃO\n"
                    "  ZX-14      120 L        Câmara 3        Conforme\n"
                    "  KR-07      45 kg        Câmara 1        Conforme\n"
                    "  VT-22      300 L        Câmara 5        Em revisão\n"
                    "  OM-09      18 kg        Câmara 2        Conforme\n\n"
                    "Próxima conferência física: 15 dias."
                ),
            },
            {
                "codigo": "D-102",
                "titulo": "Relatório de Auditoria de Contenção",
                "classificacao": "Restrito",
                "data": "02/08/2026",
                "autor": "Auditoria Interna",
                "corpo": (
                    "Resumo da auditoria semestral (fictício):\n\n"
                    "  • Câmaras auditadas: 8\n"
                    "  • Conformidade geral: 94%\n"
                    "  • Não conformidades: 2 (sensores de umidade e registro de acesso "
                    "manual na Câmara 5)\n"
                    "  • Prazo de correção: 30 dias\n\n"
                    "Recomendação: ampliar a redundância dos sensores e reforçar o "
                    "treinamento de registro de acessos."
                ),
            },
            {
                "codigo": "D-103",
                "titulo": "Plano de Contingência para Vazamento",
                "classificacao": "Restrito",
                "data": "11/09/2026",
                "autor": "Comitê de Emergências",
                "corpo": (
                    "Etapas gerais do plano (fictício):\n\n"
                    "  1. Acionar o alarme da área e isolar o setor.\n"
                    "  2. Comunicar a Diretoria e a Central de Emergências.\n"
                    "  3. Evacuar a equipe pelas saídas sinalizadas.\n"
                    "  4. Equipe especializada realiza a contenção.\n"
                    "  5. Relatório do incidente em até 24 horas.\n\n"
                    "Simulados obrigatórios a cada 90 dias."
                ),
            },
            {
                "codigo": "D-104",
                "titulo": "Orçamento Reservado de Pesquisa",
                "classificacao": "Restrito",
                "data": "25/07/2026",
                "autor": "Secretaria Executiva",
                "corpo": (
                    "Distribuição fictícia do orçamento de pesquisa do exercício:\n\n"
                    "  Monitoramento de bacias ........... R$ 4,2 milhões\n"
                    "  Contenção e segurança ............. R$ 6,8 milhões\n"
                    "  Treinamento de equipes ............ R$ 1,5 milhão\n"
                    "  Reserva estratégica ............... R$ 3,0 milhões\n\n"
                    "Liberações acima de R$ 500 mil exigem aprovação da Diretoria."
                ),
            },
        ],
    },
    3: {
        "nome": "Cofre Máximo",
        "perfil": "Ministro do Meio Ambiente",
        "descricao": "Informações estratégicas de segurança máxima. "
                     "Acesso exclusivo ao ministro.",
        "documentos": [
            {
                "codigo": "M-201",
                "titulo": "Dossiê Projeto Aurora",
                "classificacao": "ULTRASSECRETO",
                "data": "03/05/2026",
                "autor": "Gabinete do Ministro",
                "corpo": (
                    "Visão geral do programa fictício 'Aurora', que cataloga agentes "
                    "ambientais de alto risco apenas por codinome:\n\n"
                    "  • Agente 'Vespertina' (A-01) - risco regional, estoque encerrado\n"
                    "  • Agente 'Névoa Cinza' (A-02) - risco nacional, em custódia\n"
                    "  • Agente 'Raiz Negra' (A-03) - risco continental, sob vigilância\n\n"
                    "Este dossiê descreve apenas a classificação de risco e a custódia. "
                    "Nenhum detalhe técnico consta em qualquer documento do Ministério."
                ),
            },
            {
                "codigo": "M-202",
                "titulo": "Códigos de Emergência Nacional",
                "classificacao": "ULTRASSECRETO",
                "data": "14/01/2026",
                "autor": "Gabinete de Segurança Institucional",
                "corpo": (
                    "Níveis de alerta (fictícios):\n\n"
                    "  VERDE .... operação normal\n"
                    "  AMARELO .. atenção: reforço de monitoramento\n"
                    "  LARANJA .. alerta: mobilização de equipes regionais\n"
                    "  VERMELHO . emergência: ativação do Comitê Nacional\n\n"
                    "A mudança de nível depende de decisão conjunta do ministro e do "
                    "Comitê. O nível atual é VERDE."
                ),
            },
            {
                "codigo": "M-203",
                "titulo": "Mapa de Custódia dos Estoques",
                "classificacao": "ULTRASSECRETO",
                "data": "22/07/2026",
                "autor": "Diretoria de Custódia",
                "corpo": (
                    "Locais de custódia (todos fictícios):\n\n"
                    "  SITE-ALFA .... Subsolo da Sede, Brasília - 2 câmaras\n"
                    "  SITE-BRAVO ... Base Serra Dourada - 1 câmara\n"
                    "  SITE-CHARLIE . Ilha do Farol - 3 câmaras\n\n"
                    "Cada site possui vigilância 24h e acesso mediante dupla "
                    "autenticação."
                ),
            },
            {
                "codigo": "M-204",
                "titulo": "Protocolo de Desativação de Emergência",
                "classificacao": "ULTRASSECRETO",
                "data": "09/10/2026",
                "autor": "Comitê Nacional de Emergências",
                "corpo": (
                    "Em caso de ameaça iminente aos sites de custódia, o ministro pode "
                    "autorizar a desativação de emergência (fictício):\n\n"
                    "  1. Confirmação de identidade por biometria facial.\n"
                    "  2. Validação do código de emergência VERMELHO.\n"
                    "  3. Notificação simultânea às Forças de Segurança.\n"
                    "  4. Lacre dos sites e registro completo em ata.\n\n"
                    "Todo acionamento é auditado pelo Tribunal de Contas."
                ),
            },
        ],
    },
}
