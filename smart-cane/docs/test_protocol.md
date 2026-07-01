# Protocolo de Testes — Bengala Inteligente Gralha Azul

## 1. Teste em bancada (sem movimento)

Objetivo: validar módulos isoladamente antes de qualquer teste com usuário.

1. Rodar `pytest tests/` — todos os testes unitários devem passar.
2. Rodar `python scripts/calibrate_distance.py` e confirmar leituras estáveis do sensor de distância com objetos a 0,2m / 1,0m / 2,0m / 3,0m.
3. Rodar `python scripts/benchmark_latency.py --simulation` e registrar a latência média.
4. Acionar manualmente cada motor de vibração e o buzzer (via `--simulation` ou hardware) e confirmar resposta tátil/sonora.
5. Testar o botão físico: toque curto (alterna modo silencioso) e toque longo (encerra o sistema).
6. Provocar falhas propositalmente (desconectar câmera, cobrir o sensor) e confirmar que o sistema entra em modo degradado ou `ERROR` sem travar.

**Critério de aprovação:** todos os itens acima funcionam sem travamento e sem exceções não tratadas no terminal.

## 2. Teste em corredor (ambiente controlado, interno)

Objetivo: validar detecção acima da cintura em movimento lento e controlado.

1. Posicionar obstáculos acima da cintura (placa, caixa suspensa, prateleira) no percurso.
2. Caminhar em velocidade lenta/moderada com a bengala montada.
3. Registrar, para cada obstáculo: distância de detecção, nível de risco atingido, tipo de alerta (vibração esquerda/direita/central, buzzer) e latência (via logs).
4. Repetir 10 vezes por tipo de obstáculo.

**Métricas coletadas:**
- Taxa de detecção correta (obstáculo detectado antes da colisão).
- Taxa de falso positivo (alerta sem obstáculo real).
- Latência média (`logs/session_*.csv`, coluna `latency_ms`).

**Critério de aprovação:** taxa de detecção ≥ 80%, falso positivo ≤ 20%, latência média ≤ 500 ms.

## 3. Teste em ambiente urbano controlado

Objetivo: validar o protótipo em condições próximas do Dia do Desafio.

1. Definir um circuito urbano curto e previamente inspecionado (calçada com placas, marquises, mobiliário urbano, galhos).
2. Percorrer o circuito com o usuário de teste (acompanhado por um observador), seguindo o protocolo de acessibilidade do edital.
3. Registrar cada alerta emitido, o obstáculo correspondente (quando existir) e a reação do usuário.
4. Rodar o sistema por, no mínimo, 30 minutos contínuos para validar estabilidade (RF02, critério de aceitação).
5. Verificar autonomia da bateria ao final do percurso.

**Métricas coletadas:**
- Todas as métricas do teste em corredor.
- Autonomia observada (horas).
- Peso do módulo montado na bengala.
- Feedback qualitativo do usuário sobre a compreensão dos padrões de vibração/som.

**Critério de aprovação (protótipo funcional):**
- Sistema roda os 30 minutos sem travar.
- Nenhum alerta sonoro contínuo (apenas beeps curtos, conforme RF09).
- A bengala permanece 100% utilizável mesmo em caso de falha eletrônica (fail-safe, seção 17 dos requisitos).
- Logs completos gerados para os três roteiros de teste, em arquivos separados por sessão.
