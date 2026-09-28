# EyE C — Captor (Raspberry Pi)

Client Python qui tourne sur le **Raspberry Pi** : il capture des images via la caméra et les envoie au backend EyE C pour analyse NVIDIA.

## Prérequis

- Raspberry Pi OS (64-bit recommandé) avec caméra activée
- Python **3.11+**
- Stack caméra : `libcamera` / **picamera2** (préinstallé sur Raspberry Pi OS récent)
- Backend EyE C accessible sur le réseau (`BACKEND_URL`)

## Activer la caméra

1. `sudo raspi-config` → **Interface Options** → **Camera** → Enable  
2. Redémarrer si demandé  
3. Vérifier : `libcamera-hello --list-cameras`

## Installation

```bash
cd captors
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Sur le Pi, si `picamera2` n’est pas déjà présent :

```bash
sudo apt update
sudo apt install -y python3-picamera2
```

## Configuration

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `BACKEND_URL` | URL du backend (ex. `http://192.168.1.20:8000`) |
| `CAPTOR_API_KEY` | Même secret que `CAPTOR_API_KEY` côté backend |
| `CAPTOR_ID` | Identifiant unique de ce Pi (ex. `pi-captor-01`) |
| `USE_MOCK_CAMERA` | `true` pour tester sans caméra (PC / CI) |

Le fichier `.env` à la **racine du monorepo** est aussi lu si présent.

## Lancer le client

Depuis `captors/` avec le venv activé :

```bash
python main.py
```

- Une frame est capturée et envoyée toutes les **3,5 secondes**
- **Ctrl+C** arrête proprement la caméra et quitte
- En cas d’erreur réseau, l’échec est loggé et la boucle continue (adapté à une démo longue)

## Architecture locale

```
main.py  →  camera.py (JPEG)  →  uploader.py  →  POST /api/analyze (source=captor)
```

Le backend enchaîne ensuite `captor_service.py` → `nvidia_service.py`.
