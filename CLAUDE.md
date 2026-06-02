# Projet : CR de Chantier IA

## Vision produit

Application permettant à un architecte d'**enregistrer une réunion de chantier sur son téléphone**, puis de recevoir automatiquement un **compte rendu structuré, prêt à envoyer**, sans saisie manuelle.

Le problème : après chaque réunion de chantier, l'architecte passe 1-3h à rédiger le CR de mémoire ou depuis des notes manuscrites, souvent le soir. C'est chronophage, répétitif, et source d'oublis.

La solution : enregistrement audio → transcription → structuration IA → export Word/PDF.

---

## Utilisateur cible

- Architectes en cabinet (indépendants ou petites structures 2-10 personnes)
- Maîtres d'œuvre
- Conducteurs d'opérations
- Marché France : ~30 000 cabinets d'architecture, ~70 000 architectes inscrits à l'Ordre

## Validation terrain

- Problème confirmé directement par un architecte utilisateur
- Gestion actuelle : 100% analogique (notes manuscrites, mémoire, parfois dictaphone)
- Aucun outil spécifique au format CR de chantier français n'existe aujourd'hui

---

## Format d'un CR de chantier (structure standard française)

```
COMPTE RENDU DE CHANTIER N°XX
Opération : [nom du projet]
Date : [date]
Lieu : [adresse chantier]

PRÉSENTS :
- [Nom], [Qualité], [Entreprise/Cabinet]
- ...

ABSENTS EXCUSÉS :
- ...

POINTS ABORDÉS PAR LOT :

LOT 01 - GROS ŒUVRE (entreprise X)
  - [Point soulevé]
  - Décision : [décision prise]
  - Action : [qui fait quoi avant quelle date]

LOT 02 - CHARPENTE (entreprise Y)
  - ...

QUESTIONS / DIVERS :
  - ...

PROCHAINE RÉUNION :
  - Date : [date]
  - Lieu : [lieu]

Diffusion : [liste des destinataires]
```

---

## Architecture technique

### Pipeline complet

```
1. Enregistrement audio (téléphone, ~30-90 min)
        ↓
2. Upload fichier audio (MP3/M4A/WAV)
        ↓
3. Transcription : OpenAI Whisper API
   - Endpoint : POST https://api.openai.com/v1/audio/transcriptions
   - Modèle : whisper-1
   - Coût : 0,006$/minute → ~0,30-0,54$ par réunion d'1h
   - Supporte le français nativement
        ↓
4. Structuration LLM : Claude ou GPT-4o
   - Prompt système : voir section "Prompts" ci-dessous
   - Input : transcription brute + contexte projet
   - Output : JSON structuré par lot
        ↓
5. Génération document : export Word (.docx) ou PDF
   - Librairie Python : python-docx
   - Template personnalisable par cabinet
        ↓
6. Envoi : téléchargement direct ou envoi par email
```

### Stack recommandée MVP

```
Backend  : Python + FastAPI
Frontend : React ou Next.js (simple, mobile-first)
Audio    : Web Audio API (enregistrement in-browser) ou upload fichier
Transcription : OpenAI Whisper API
LLM      : Claude claude-sonnet-4-20250514 (via API Anthropic)
Export   : python-docx pour Word, reportlab ou weasyprint pour PDF
Auth     : Magic link email (pas de password)
BDD      : PostgreSQL (Supabase)
Hébergement : Railway ou Render (simple, pas besoin HDS)
```

---

## Prompts

### Prompt système (structuration du CR)

```
Tu es un assistant spécialisé dans la rédaction de comptes rendus de chantier pour architectes français.

À partir de la transcription d'une réunion de chantier, tu dois produire un compte rendu structuré au format JSON.

Règles :
- Identifie tous les intervenants mentionnés (nom, qualité, entreprise si mentionné)
- Classe chaque point soulevé par lot (gros œuvre, charpente, électricité, plomberie, menuiserie, etc.)
- Pour chaque point, identifie : la description, la décision prise (si applicable), l'action à mener, le responsable, le délai
- Identifie la date et le lieu de la prochaine réunion si mentionnés
- En cas d'ambiguïté, garde les deux versions possibles avec une note [À VÉRIFIER]
- Ne jamais inventer d'informations non présentes dans la transcription

Format de sortie JSON :
{
  "numero_cr": null,
  "date_reunion": "YYYY-MM-DD ou null",
  "lieu": "adresse ou null",
  "presents": [{"nom": "", "qualite": "", "entreprise": ""}],
  "absents": [{"nom": "", "qualite": "", "entreprise": ""}],
  "lots": [
    {
      "numero": "01",
      "nom": "GROS ŒUVRE",
      "entreprise": "",
      "points": [
        {
          "description": "",
          "decision": "",
          "action": "",
          "responsable": "",
          "delai": ""
        }
      ]
    }
  ],
  "divers": [""],
  "prochaine_reunion": {"date": "", "lieu": ""},
  "diffusion": [""]
}
```

### Prompt utilisateur

```
Voici la transcription d'une réunion de chantier.
Projet : {nom_projet}
Lots présents sur ce chantier : {liste_lots}

Transcription :
{transcription}

Produis le compte rendu structuré en JSON.
```

---

## Fonctionnalités MVP (v1)

- [ ] Upload fichier audio (MP3, M4A, WAV, jusqu'à 500MB)
- [ ] Transcription automatique via Whisper
- [ ] Structuration en CR via LLM
- [ ] Affichage du CR structuré avec possibilité d'édition inline
- [ ] Export Word (.docx) avec template standard
- [ ] Historique des CR par projet
- [ ] Gestion simple des projets (nom, adresse, liste des lots, intervenants récurrents)

## Fonctionnalités v2

- [ ] Enregistrement audio directement dans l'app (mobile)
- [ ] Template de CR personnalisable par cabinet (logo, couleurs, format)
- [ ] Envoi du CR par email directement depuis l'app (avec liste de diffusion par projet)
- [ ] Comparaison CR N vs CR N-1 (points récurrents non résolus)
- [ ] Suivi des actions ouvertes (tableau de bord des réserves non levées)
- [ ] Export PDF signé
- [ ] Numérotation automatique des CR

## Fonctionnalités v3

- [ ] Application mobile native (iOS/Android) avec enregistrement intégré
- [ ] Identification automatique des intervenants par voix (speaker diarization)
- [ ] Intégration calendrier (rappel avant réunion, envoi CR après)
- [ ] Mémoire des intervenants récurrents entre projets

---

## Coûts API estimés

| Usage | Coût par CR |
|-------|------------|
| Whisper (1h réunion) | ~0,36$ |
| LLM structuration (Claude Haiku) | ~0,02$ |
| **Total par CR** | **~0,38$** |

Pour 100 utilisateurs × 4 réunions/mois = 400 CR/mois → ~152$/mois de coûts API.

---

## Modèle économique

- **Freemium** : 3 CR/mois gratuits, illimité à 29€/mois
- **Par cabinet** : 49€/mois pour jusqu'à 5 utilisateurs
- **Cible break-even** : ~50 cabinets payants

## Pricing de référence marché

- Un architecte facture 80-150€/heure
- Un CR prend 1-3h = 80-450€ de temps architecte par réunion
- L'outil économise ~2h/CR → ROI immédiat et évident à la vente

---

## Go-To-Market

### Phase 1 — 0 à 10 clients (validation)
- Appels directs à des architectes locaux (réseau personnel)
- Offre : 3 mois gratuits en échange de feedback
- Objectif : valider que le CR généré est "bon du premier coup" à 80%+

### Phase 2 — 10 à 100 clients
- LinkedIn ciblé (architectes, maîtres d'œuvre)
- Partenariat avec l'Ordre des Architectes (régions)
- Contenu : "avant/après" d'un CR rédigé en 30 secondes vs 2h

### Phase 3 — 100+ clients
- Intégration dans les outils de gestion de projet existants (PlanRadar, etc.)
- Revendeurs / prescripteurs (logiciels de gestion de cabinet)

---

## Obstacles et risques

| Obstacle | Mitigation |
|----------|-----------|
| Qualité audio mauvaise (bruit de chantier) | Whisper est robuste au bruit ; option de correction manuelle |
| CR incomplet (oublis dans la transcription) | Affichage transcription brute + UI d'édition rapide |
| Réticence à enregistrer (RGPD) | Mention légale d'enregistrement, données supprimées après export |
| Adoption lente (habitudes ancrées) | Démo live en 5 min suffit à convaincre |

---

## Fichiers du projet

```
CLAUDE.md          Ce fichier
src/
  api/             Backend FastAPI
  frontend/        React app
  transcription/   Module Whisper
  structuration/   Module LLM → JSON
  export/          Module Word/PDF
```
