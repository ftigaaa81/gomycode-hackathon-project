# EyE C

**EyE C** est un assistant vocal pour personnes malvoyantes : des capteurs caméra (Raspberry Pi et/ou téléphone) envoient des images au backend, qui s’appuie sur **Gemini Vision** pour produire des alertes courtes, priorisées, restituées à la voix sur mobile.

## Flux de données

Le mobile peut **aussi servir de captor de secours** via sa propre caméra si aucun Raspberry Pi n’est disponible.

```
┌─────────────────────┐     POST /api/analyze      ┌──────────────────┐
│ Captor Raspberry Pi │ ─────────────────────────► │                  │
│ (captors/main.py)   │   source=captor            │  Backend FastAPI │
└─────────────────────┘                            │  captor_service  │
                                                   │        │         │
┌─────────────────────┐     POST /api/analyze      │        ▼         │
│ Mobile (secours)    │ ─────────────────────────► │  nvidia_service  │──► Gemini Vision
│ frameCapture.ts     │   source=mobile            │        │         │
└─────────────────────┘                            │        ▼         │
                                                   │ priority_engine  │
                                                   │   (cooldowns)    │
                                                   └────────┬─────────┘
                                                            │ JSON AnalyzeResponse
                                                            ▼
                                                   ┌──────────────────┐
                                                   │ Mobile Expo      │
                                                   │ TTS + file voix  │
                                                   │ usePriorityQueue │
                                                   └──────────────────┘
```

Mode **démo jury** : triple-tap sur le titre « EyE C » dans l’app → `GET /api/demo/scene/random` (scénarios curatés, sans appel Gemini).

## Structure du monorepo

```
eye-c/
├── mobile/          # React Native + Expo (TypeScript)
├── backend/         # FastAPI (Python 3.11+)
├── captors/         # Client Python Raspberry Pi
├── demo/            # Scènes et réponses attendues
└── docs/            # Fiche projet, documentation
```

## Prérequis

- **Node.js** 18+ et npm (mobile)
- **Python** 3.11+ (backend, captors, scripts)
- Clé API **Gemini** (backend)
- **Raspberry Pi** + caméra (optionnel mais recommandé pour la démo matérielle)
- Réseau local ou internet stable (pas de mode hors-ligne complet)

## Configuration

Copiez les fichiers d’exemple **sans jamais commiter** de `.env` :

```bash
cp .env.example .env
cp backend/.env.example backend/.env    # optionnel si vous n’utilisez que .env racine
cp captors/.env.example captors/.env
cp mobile/.env.example mobile/.env
```

Les services lisent en priorité le `.env` de leur dossier, puis le `.env` à la **racine** du monorepo.

| Variable | Composant | Rôle |
|----------|-----------|------|
| `GEMINI_API_KEY` | backend | Authentification Gemini Vision (à garder côté serveur) |
| `CAPTOR_API_KEY` | backend, captors | Secret header `X-Captor-API-Key` |
| `BACKEND_URL` | captors | URL du backend |
| `CAPTOR_ID` | captors | Identifiant du Pi |
| `EXPO_PUBLIC_BACKEND_URL` | mobile | URL du backend (IP LAN du PC; équivalent mobile de `BACKEND_URL`) |
| `EXPO_PUBLIC_DEMO_MODE` | mobile | Force le mode démo (`true` ou `false`; équivalent mobile de `DEMO_MODE`) |
| `APP_ENV`, `LOG_LEVEL` | backend | Logs (JSON en production) |
| `USE_MOCK_CAMERA` | captors | `true` sans matériel Pi |

## Quick start

Trois terminaux (après avoir configuré `GEMINI_API_KEY` dans `backend/.env`, les variables mobile dans `mobile/.env`, et installé les dépendances).

### 1. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Vérification : `curl http://127.0.0.1:8000/health`

### 2. Mobile

```bash
cd mobile
npm install
# EXPO_PUBLIC_BACKEND_URL=http://<IP-LAN-PC>:8000 dans mobile/.env
# EXPO_PUBLIC_DEMO_MODE=false pour utiliser l'analyse Gemini
npx expo start
```

Scannez le QR code avec **Expo Go** sur un téléphone (même Wi‑Fi que le backend).

### 3. Captors (Raspberry Pi ou dev avec mock)

```bash
cd captors
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # BACKEND_URL, CAPTOR_API_KEY, CAPTOR_ID
python main.py
```

Sur PC sans Pi : `USE_MOCK_CAMERA=true` dans `captors/.env`.

### Scripts utiles (backend)

```bash
# Test Gemini réel (image locale)
python backend/scripts/test_nvidia_live.py chemin/vers/image.jpg

# Simulation 10 frames (anti-spam / timing)
python backend/scripts/simulate_scenario.py --base-url http://127.0.0.1:8000
```

## Limitations connues

- **Latence réseau** : capture → backend → Gemini → TTS ; le ressenti utilisateur dépend du Wi‑Fi / 4G et de la disponibilité de l’API.
- **Dépendance à un modèle vision hébergé** : sans Gemini (ou en cas d’erreur), le backend renvoie un **fallback** générique ou le mode **démo** curaté — pas d’analyse locale embarquée.
- **Matériel captor** : le scénario nominal repose sur un **Raspberry Pi** caméra ; le mobile compense partiellement mais avec une autonomie et un angle de vue différents.
- **Pas de mode hors-ligne complet** : backend et inférence distante requis pour l’analyse réelle ; seuls le TTS et le mode démo local atténuent une coupure réseau.

## Tests backend

```bash
cd backend && python3 -m pytest
```

## Contribuer

Voir [CONTRIBUTING.md](./CONTRIBUTING.md) (Conventional Commits).

## Documentation

- [docs/project_card.md](./docs/project_card.md) — fiche projet hackathon (GOMYCODE)

## Licence

À définir par l’équipe hackathon.
