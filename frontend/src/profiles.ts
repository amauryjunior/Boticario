// Perfis de necessidade (espelham app/agents/knowledge.py PROFILES).
export const PROFILES: { id: string; label: string }[] = [
  { id: "cegueira", label: "Pessoa cega" },
  { id: "baixa_visao", label: "Baixa visão" },
  { id: "daltonismo", label: "Daltonismo" },
  { id: "motora", label: "Deficiência motora" },
  { id: "artrite", label: "Artrite / baixa força" },
  { id: "destreza_reduzida", label: "Destreza fina reduzida" },
  { id: "idoso", label: "Pessoa idosa (60+)" },
  { id: "neurodivergente", label: "Neurodivergente" },
  { id: "cognitiva", label: "Deficiência cognitiva" },
  { id: "situacional", label: "Uso situacional difícil" },
];

export const COMPONENTS = [
  "frasco", "tampa", "rotulo", "valvula", "atomizador",
  "pump", "caixa", "folheto", "aplicador", "lacre", "refil",
];
