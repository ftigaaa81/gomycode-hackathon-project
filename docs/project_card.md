# EyE C — Fiche projet (GOMYCODE)

## Problème

Les personnes malvoyantes doivent souvent interpréter rapidement un environnement changeant (obstacles, escaliers, véhicules, signalétique) sans retour visuel immédiat. Les solutions génériques (GPS, cannes) ne décrivent pas la scène devant elles en langage naturel, et les assistants vocaux classiques ne « voient » pas le contexte local.

## Solution

**EyE C** combine trois briques : un **captor Raspberry Pi** (caméra) envoie des images toutes les ~3,5 s au **backend FastAPI** ; un modèle **vision NVIDIA** produit une analyse JSON courte (urgence, message, objet principal, texte éventuel) ; l’**application mobile Expo** lit le message à voix haute avec des règles de priorité (danger > attention > normal). Si le Pi est indisponible, le **téléphone sert de captor de secours** via sa caméra. Un **mode démo** (scènes curatées) sécurise les présentations jury lorsque le réseau ou l’API est instable.

## Stack technique

- **Mobile** : React Native, Expo, TypeScript strict, expo-camera, expo-speech, expo-haptics  
- **Backend** : Python 3.11+, FastAPI, Pydantic, httpx, priority engine, fallbacks  
- **Captors** : Python, picamera2 (Pi), envoi HTTP vers `/api/analyze`  
- **IA** : NVIDIA Build / NIM vision (prompt système contraint en JSON)

## IA responsable

- **Pas de décision automatique irréversible** : l’assistant **parle** des indices ; l’utilisateur reste acteur (mobilité, cane, accompagnement).  
- **Validation implicite par cooldowns** : le moteur de priorité limite la verbosité (anti-spam) ; le danger peut interrompre un message en cours.  
- **Transparence** : messages courts, fallback explicite si le modèle échoue, mode démo assumé pour la démo hackathon.  
- **Sécurité des secrets** : clés NVIDIA et captor uniquement via variables d’environnement.

## Impact visé

Réduire l’anxiété en déplacement intérieur/extérieur en donnant **une information à la fois**, orientée **sécurité physique**, avec une architecture extensible (plusieurs captors, scènes de test, scripts de rehearsal). L’équipe cible une **preuve de concept démontrable en 90 secondes** : une alerte danger (escalier, véhicule), une lecture de panneau, et la bascule captor Pi / caméra mobile. Au-delà du hackathon, la même stack pourrait accueillir d’autres modèles ou une réduction de débit vidéo pour limiter la latence. EyE C reste un **assistant**, pas un système autonome de navigation : il complète la cane, le chien guide ou l’accompagnant humain.
