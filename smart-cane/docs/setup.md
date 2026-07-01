# Instalação e Configuração — Raspberry Pi OS Lite

## 1. Instalar o Raspberry Pi OS Lite

1. Baixe o Raspberry Pi Imager e grave o **Raspberry Pi OS Lite (64-bit)** no cartão microSD.
2. Nas opções avançadas do Imager, habilite SSH e configure usuário/senha e Wi-Fi (apenas para a instalação inicial — o sistema roda offline em produção).
3. Faça o primeiro boot e conecte via SSH: `ssh pi@<ip-do-raspberry>`.

## 2. Atualizar o sistema

```bash
sudo apt update && sudo apt full-upgrade -y
```

## 3. Ativar a câmera e o I2C

```bash
sudo raspi-config
```
- `Interface Options` → `Camera` → habilitar.
- `Interface Options` → `I2C` → habilitar.
- Reinicie: `sudo reboot`.

Verifique o I2C após reiniciar:
```bash
sudo apt install -y i2c-tools
i2cdetect -y 1
```
Você deve ver o endereço do VL53L1X (`0x29`) e/ou do MPU-6050 (`0x68`) na tabela.

## 4. Instalar dependências de sistema

```bash
sudo apt install -y python3-venv python3-pip python3-picamera2 --no-install-recommends
```

## 5. Clonar o projeto e criar o ambiente virtual

```bash
git clone <repositorio>
cd smart-cane
python3 -m venv .venv --system-site-packages   # dá acesso ao picamera2 instalado via apt
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 6. Testar em modo simulação (sem hardware)

```bash
python src/main.py --simulation
```

## 7. Calibrar sensores (com hardware conectado)

```bash
python scripts/calibrate_distance.py
```

## 8. Executar com hardware real

```bash
python src/main.py --config configs/config.yaml
```

## 9. Executar como serviço systemd (inicialização automática)

```bash
sudo cp systemd/smart-cane.service /etc/systemd/system/smart-cane.service
sudo systemctl daemon-reload
sudo systemctl enable smart-cane.service
sudo systemctl start smart-cane.service
```

Verificar status e logs do serviço:
```bash
sudo systemctl status smart-cane.service
journalctl -u smart-cane.service -f
```

> Ajuste `WorkingDirectory`, `ExecStart` e `User` em `systemd/smart-cane.service` caso o projeto não esteja em `/home/pi/smart-cane`.
