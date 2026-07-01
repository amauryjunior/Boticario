# Ligação dos Componentes — Bengala Inteligente Gralha Azul

## Tabela de pinos GPIO (BCM)

| Componente | Pino GPIO (BCM) | Alimentação | Observações |
|---|:---:|:---:|---|
| Motor de vibração — esquerdo | GPIO17 | via driver/transistor | PWM — não ligar o motor direto no GPIO |
| Motor de vibração — direito | GPIO27 | via driver/transistor | PWM — idem acima |
| Buzzer passivo | GPIO22 | 3V3 | Sinal digital/PWM |
| Sensor ToF VL53L1X | SDA=GPIO2, SCL=GPIO3 | 3V3 | Barramento I2C |
| Sensor ultrassônico HC-SR04 (alternativa) | Trigger=GPIO23, Echo=GPIO24 | 5V (Echo requer divisor de tensão para 3V3) | Ver seção abaixo |
| Botão físico | GPIO5 | 3V3 (pull-up interno via gpiozero) | Toque curto / toque longo |
| Câmera CSI 5MP | Conector CSI dedicado | 3V3 | Não usa GPIO |
| IMU MPU-6050/BNO055 | SDA=GPIO2, SCL=GPIO3 | 3V3 | Compartilha o barramento I2C com o VL53L1X (endereços distintos) |

> Os números de pino acima refletem os valores padrão em `configs/config.yaml`. Se usar outros GPIOs, atualize a fiação e o arquivo de configuração juntos.

## Motores de vibração

Motores de vibração (coin motors) consomem mais corrente do que um GPIO fornece com segurança. Use um transistor NPN (ex.: 2N2222) ou um driver dedicado (ex.: DRV2605L), com o GPIO apenas controlando a base/enable:

```
GPIO17 --[resistor 1k]--> Base do transistor
Motor(+) --> Bateria (+)
Motor(-) --> Coletor do transistor
Emissor do transistor --> GND
Diodo de proteção (flyback) em paralelo com o motor
```

O motor direito segue o mesmo esquema, usando GPIO27.

## Buzzer

Buzzer passivo ligado diretamente ao GPIO22 e ao GND é suficiente para o protótipo (baixa corrente). Para maior volume, use também um transistor de chaveamento.

## Sensor de distância

### VL53L1X (recomendado — I2C)
- VIN → 3V3
- GND → GND
- SDA → GPIO2 (SDA1)
- SCL → GPIO3 (SCL1)

### HC-SR04 (alternativa — ultrassônico)
- VCC → 5V
- GND → GND
- Trig → GPIO23
- Echo → GPIO24 **através de um divisor de tensão** (ex.: resistores 1kΩ/2kΩ), pois o Echo opera em 5V e o GPIO do Raspberry Pi é 3V3.

Selecione o backend em `configs/config.yaml` com `distance_sensor.type: "vl53l1x"` ou `"hc-sr04"`.

## Câmera

Conectar o módulo CSI 5MP diretamente ao conector CSI do Raspberry Pi Zero 2 W, respeitando a orientação da fita flex (contatos voltados para a placa de circuito da câmera).

## Cuidados com a bateria

- Utilizar bateria Li-Po **com circuito de proteção** (BMS) contra sobrecarga, descarga profunda e curto-circuito.
- Nunca conectar a bateria com polaridade invertida.
- Utilizar um regulador/step-down adequado para alimentar o Raspberry Pi Zero 2 W (5V/2.5A recomendado).
- Monitorar a tensão da bateria (via ADC, se disponível) para acionar o estado `LOW_BATTERY`.
- Acomodar a bateria dentro do módulo acoplado à bengala, protegida por um invólucro rígido, longe de impactos.
