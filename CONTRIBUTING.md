# Contributing

Merci de contribuer à **EyE C** pendant le hackathon. Pour garder l’historique Git lisible pour toute l’équipe (4 personnes), nous utilisons **Conventional Commits**.

## Format

```
<type>(<scope optionnel>): <description courte>
```

Types autorisés :

| Type     | Usage |
|----------|--------|
| `feat`   | Nouvelle fonctionnalité |
| `fix`    | Correction de bug |
| `chore`  | Maintenance, dépendances, config, structure |
| `docs`   | Documentation uniquement |

Exemples :

- `feat(mobile): add voice feedback on scene description`
- `fix(backend): handle missing captor API key`
- `chore: bump expo sdk`
- `docs: update captor setup on Raspberry Pi`

## Bonnes pratiques

- Messages en **impératif**, en **anglais** ou **français** (restez cohérents au sein d’une PR).
- Un commit = une intention claire ; évitez les commits fourre-tout.
- Ne commitez **jamais** de secrets : utilisez `.env` (ignoré) et documentez les clés dans `.env.example`.
