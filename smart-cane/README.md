# Bengala Inteligente Gralha Azul — Firmware

Software embarcado de um módulo acoplável a uma bengala tradicional para
pessoas cegas ou com baixa visão. O sistema detecta e antecipa obstáculos
**estáticos acima da linha da cintura** (placas, galhos, marquises, objetos
suspensos, mobiliário urbano) e alerta o usuário por vibração direcional e/ou
som curto — operando **100% offline**, com fail-safe: a bengala continua
100% utilizável mesmo em caso de falha eletrônica (ver seção "Fail-safe").

## Hardware necessário

Versão principal (protótipo funcional):

- Raspberry Pi Zero 2 W
- Câmera CSI 5MP
- Sensor de distância: ToF VL53L1X (recomendado) ou ultrassônico HC-SR04
- IMU MPU-6050 (opcional, usado para economia de energia e contexto de movimento)
- 2 motores de vibração (esquerdo/direito)
- Buzzer passivo
- Botão físico liga/desliga / modo
- Bateria Li-Po com circuito de proteção (BMS)

Ver `docs/wiring.md` para o esquema completo de ligação.

## Arquitetura

```
smart-cane/
├── src/
│   ├── main.py              # orquestrador — máquina de estados e loop principal
│   ├── config.py            # leitura/gravação de configs/config.yaml
│   ├── camera/               # captura de frames (RF02) e pré-processamento/ROI (RF05)
│   ├── ai/                   # detector de obstáculos: tflite | heuristic | simulated (RF03)
│   ├── sensors/               # sensor de distância (RF04), IMU
│   ├── fusion/                # fusão visão+distância e nível de risco (RF06/RF07)
│   ├── alerts/                 # motores de vibração (RF08) e buzzer (RF09)
│   ├── power/                  # gestão de energia (RNF05)
│   ├── logging/                # logs de eventos para validação técnica (RF12)
│   └── utils/                  # timing e self-test
├── models/                     # modelo TFLite (não incluso — ver models/README.md)
├── configs/config.yaml         # toda a configuração do sistema
├── tests/                      # testes unitários (pytest)
├── scripts/                    # calibração, benchmark de latência, demo
└── docs/                       # ligação, instalação, protocolo de testes
```

Cada camada (sensor de distância, modelo de IA, hardware de alerta) é
intercambiável via `configs/config.yaml`, sem precisar reescrever o sistema
(RNF06) — por exemplo, trocar `distance_sensor.type` de `vl53l1x` para
`hc-sr04`, ou adicionar um `obstacle_detector.tflite` treinado sem alterar
`src/ai/detector.py`.

## Instalação

```bash
git clone <repositorio>
cd smart-cane
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Para instalação completa no Raspberry Pi (SO, câmera, I2C, systemd), veja
`docs/setup.md`.

## Execução

Modo real (hardware conectado):
```bash
python src/main.py --config configs/config.yaml
```

Modo simulação (sem hardware — desenvolvimento e demonstração):
```bash
python src/main.py --simulation
# ou:
./scripts/run_demo.sh
```

No modo simulação, distâncias e detecções fictícias são geradas e os
motores/buzzer são "virtuais" (eventos impressos/registrados em vez de
acionar GPIO real), permitindo validar toda a lógica de risco e alerta sem
um Raspberry Pi conectado.

## Calibração

```bash
python scripts/calibrate_distance.py
```
Coleta amostras do sensor de distância, permite ajustar a ROI da câmera e o
limiar de confiança da IA, e salva tudo de volta em `configs/config.yaml`.

## Benchmark de latência

```bash
python scripts/benchmark_latency.py --simulation
```
Mede o tempo de captura, inferência, leitura do sensor, decisão e latência
total por ciclo. Meta: ≤ 500 ms (aceitável), ≤ 200 ms (ideal).

## Testes

```bash
pytest tests/
```
Cobre a estimativa de risco (`risk_estimator`), o controlador de alertas
(`alert_controller`) e a fusão sensorial (`sensor_fusion`), incluindo casos
de fallback (sem câmera, sem sensor de distância, baixa confiança, fora da
ROI) e modo simulado.

## Máquina de estados

`BOOT → SELF_TEST → READY → SCANNING ⇄ ALERT_ATTENTION/MODERATE/CRITICAL`,
com `LOW_BATTERY`, `ERROR` e `SHUTDOWN` tratados à parte. Ver `src/main.py`.

## Fail-safe

- Falha na câmera: sistema tenta reiniciar o módulo; obstáculo continua
  sendo avaliado pelo sensor de distância.
- Falha no sensor de distância ou na IA: sistema degrada graciosamente para
  os módulos ainda disponíveis (visão apenas ou distância apenas).
- Falha crítica (câmera **e** sensor de distância indisponíveis): autoteste
  emite um beep de erro e o sistema não entra em varredura — mas a bengala
  física permanece 100% utilizável, já que o módulo é apenas acoplado, nunca
  substitui a bengala.
- Nenhum alerta sonoro contínuo é emitido — apenas beeps curtos — para não
  atrapalhar a orientação auditiva do usuário.

## Limitações conhecidas

- Não há modelo de IA treinado incluso neste repositório (`models/` está
  vazio) — o detector opera em modo heurístico (contornos/OpenCV) ou
  simulado até que um `obstacle_detector.tflite` seja adicionado (ver
  `models/README.md`).
- Não há hardware de bateria com ADC integrado no MVP; `battery_status` fica
  como `"unknown"` até que um circuito de leitura de tensão seja conectado
  (ver `src/power/power_manager.py`).
- A fusão de risco usa regras determinísticas simples (RF06), não um modelo
  de fusão probabilístico — adequado ao escopo do protótipo do Dia do
  Desafio, mas não a um produto final.
