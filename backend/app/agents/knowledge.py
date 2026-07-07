"""Base de conhecimento de acessibilidade de embalagens de beleza.

Codifica heurísticas de barreiras por componente e por perfil, alternativas de
tampa (RF-011), soluções mínima/intermediária/premium (RF-023) e mapeamento
normativo com status (RF-016). É a inteligência do motor offline e também serve
de guardrail/base de fatos para os agentes ADK.
"""
from __future__ import annotations

# Perfis de necessidade (RF-009)
PROFILES = {
    "cegueira": "pessoa cega",
    "baixa_visao": "pessoa com baixa visão",
    "daltonismo": "pessoa daltônica",
    "motora": "pessoa com deficiência motora",
    "artrite": "pessoa com artrite / baixa força",
    "destreza_reduzida": "pessoa com destreza fina reduzida",
    "idoso": "pessoa idosa (60+)",
    "neurodivergente": "pessoa neurodivergente",
    "cognitiva": "pessoa com deficiência cognitiva",
    "situacional": "uso situacional difícil",
}

# Alternativas de tampa por necessidade (RF-011)
CAP_ALTERNATIVES = {
    "asas": "tampa de asas — destreza limitada e força reduzida",
    "flip_top": "flip-top — destreza limitada / artrite",
    "rosca_relevo": "rosca com relevo — deficiência visual e destreza limitada",
    "press_to_open": "press-to-open — artrite / força reduzida",
    "magnetica": "tampa magnética com feedback sonoro — máxima autonomia",
}

# Normas/guidelines com status (RF-016). status: confirmada | referencia_design |
# hipotese | aplicavel_com_ressalva | pendente_validacao
STANDARDS = {
    "WCAG22": {
        "ref": "WCAG 2.2 (W3C) — contraste e legibilidade (referência p/ rótulo digital)",
        "status": "referencia_design",
    },
    "LBI": {
        "ref": "Lei Brasileira de Inclusão — Lei nº 13.146/2015",
        "status": "aplicavel_com_ressalva",
    },
    "ANVISA": {
        "ref": "ANVISA — rotulagem de cosméticos (legislação vigente)",
        "status": "pendente_validacao",
    },
    "EAA": {
        "ref": "Diretiva UE 2019/882 — European Accessibility Act",
        "status": "aplicavel_com_ressalva",
    },
    "NBR9050": {
        "ref": "ABNT NBR 9050 — acessibilidade (referência de design)",
        "status": "referencia_design",
    },
}

# Regras: cada regra descreve uma barreira potencial, os perfis impactados, a
# dimensão de score afetada e as alternativas de solução.
# Campo `applies`: função lambda(product, components) -> bool
RULES = [
    {
        "id": "tampa_dificil",
        "dimension": "Operabilidade e abertura",
        "component": "tampa",
        "barrier": "Abertura difícil / tampa exige força ou destreza fina",
        "profiles": ["artrite", "destreza_reduzida", "motora", "idoso"],
        "impact": "Impede uso independente do produto",
        "option_min": "Relevo/textura antiderrapante na lateral da tampa",
        "option_mid": "Flip-top com textura ou tampa de asas",
        "option_premium": "Tampa magnética com feedback sonoro de fechamento",
        "standard": "NBR9050",
        "trigger_caps": {None, "rosca", "screw", "rosca_simples"},
    },
    {
        "id": "rotulo_contraste",
        "dimension": "Leitura, contraste e rotulagem",
        "component": "rotulo",
        "barrier": "Baixo contraste / fonte pequena no rótulo",
        "profiles": ["baixa_visao", "idoso", "daltonismo"],
        "impact": "Dificulta ou impede a leitura das informações",
        "option_min": "Aumentar tamanho de fonte e contraste (mín. AA)",
        "option_mid": "Alto contraste + pictogramas + linguagem simples",
        "option_premium": "QR acessível + audiodescrição + braille",
        "standard": "WCAG22",
    },
    {
        "id": "identificacao_tatil",
        "dimension": "Identificação tátil e multisensorial",
        "component": "frasco",
        "barrier": "Ausência de identificação tátil do produto",
        "profiles": ["cegueira", "baixa_visao"],
        "impact": "Impede identificar o produto sem visão",
        "option_min": "Marca tátil simples (relevo/entalhe) no frasco",
        "option_mid": "Textura codificada por linha de produto",
        "option_premium": "Etiqueta olfativa + mapa tátil + NaviLens",
        "standard": "LBI",
    },
    {
        "id": "braille_ausente",
        "dimension": "Identificação tátil e multisensorial",
        "component": "rotulo",
        "barrier": "Ausência de braille ou alternativa digital acessível",
        "profiles": ["cegueira"],
        "impact": "Informação essencial inacessível a pessoas cegas",
        "option_min": "QR code com conteúdo acessível",
        "option_mid": "Braille no nome do produto + QR",
        "option_premium": "Braille completo + audiodescrição via NFC/QR",
        "standard": "LBI",
    },
    {
        "id": "instrucoes_complexas",
        "dimension": "Clareza das instruções",
        "component": "folheto",
        "barrier": "Instruções complexas / sem linguagem simples",
        "profiles": ["cognitiva", "neurodivergente", "idoso"],
        "impact": "Uso incorreto por incompreensão",
        "option_min": "Reescrever em linguagem simples",
        "option_mid": "Passo a passo com pictogramas",
        "option_premium": "Vídeo em Libras + áudio + pictogramas",
        "standard": "WCAG22",
    },
    {
        "id": "feedback_fechamento",
        "dimension": "Segurança e risco de uso incorreto",
        "component": "tampa",
        "barrier": "Ausência de feedback de fechamento",
        "profiles": ["cegueira", "baixa_visao", "cognitiva"],
        "impact": "Risco de vazamento / uso incorreto",
        "option_min": "Clique audível ao fechar",
        "option_mid": "Clique + batente tátil",
        "option_premium": "Feedback sonoro e tátil confirmando vedação",
        "standard": "NBR9050",
    },
    {
        "id": "sustentabilidade_refil",
        "dimension": "Sustentabilidade e refil",
        "component": "frasco",
        "barrier": "Sem opção de refil / reciclabilidade",
        "profiles": ["situacional"],
        "impact": "Maior custo e desperdício ao usuário recorrente",
        "option_min": "Informar reciclabilidade no rótulo",
        "option_mid": "Oferecer refil da mesma linha",
        "option_premium": "Sistema de refil reutilizável com identificação tátil",
        "standard": "EAA",
    },
]

# Itens de checklist adicionais que sempre entram para dar cobertura ao RF-012.
BASELINE_CHECKLIST = [
    ("Inovação inclusiva", "Uso de solução inovadora de acessibilidade", "a_validar",
     "Requer avaliação de portfólio de soluções inovadoras."),
    ("Evidência/teste com usuário", "Teste realizado com pessoas com deficiência", "nao_atende",
     "Nenhum teste com PcD registrado neste produto (RF-030)."),
]
