"# LogAnalyzer Pro" 
# LogAnalyzer Pro

Pipeline d'analyse et d'archivage de logs applicatifs — TP Python L3, 2026.

---

## 1. Description du projet et objectif

**LogAnalyzer Pro** est un outil CLI (Command Line Interface) Python qui automatise la supervision des logs applicatifs générés quotidiennement par des services DevOps. Il :

- Scanne un dossier de fichiers `.log` et filtre les entrées par niveau de criticité (`ERROR`, `WARN`, `INFO`, `ALL`)
- Calcule des statistiques (totaux, répartition par niveau, Top 5 des erreurs les plus fréquentes)
- Génère un rapport structuré au format **JSON** horodaté
- Archive les fichiers traités dans une archive **`.tar.gz`** compressée
- Nettoie automatiquement les anciens rapports selon une politique de rétention configurable
- Est planifiable via **Cron** pour s'exécuter sans intervention humaine

---

## 2. Prérequis et installation

- **Python** ≥ 3.10 (testé avec 3.14)
- **Aucune dépendance externe** — uniquement la bibliothèque standard Python
- Modules utilisés : `argparse`, `glob`, `os`, `platform`, `collections`, `json`, `datetime`, `tarfile`, `shutil`, `subprocess`, `time`, `sys`

```bash
# Vérifier la version Python
python3 --version

# Cloner le dépôt
git clone https://github.com/<organisation>/loganalyzer.git
cd loganalyzer
```

Aucun `pip install` n'est requis.

---

## 3. Utilisation — Exemples de commandes

### Lancer le pipeline complet

```bash
# Analyser tous les niveaux, archive dans backups/, rétention 30 jours
python3 main.py --source logs_test/

# Filtrer uniquement les erreurs
python3 main.py --source logs_test/ --niveau ERROR

# Spécifier le dossier de destination et la rétention
python3 main.py --source /var/logs/app --niveau WARN --dest /var/backups/loganalyzer --retention 15
```

### Arguments disponibles

| Argument      | Défaut     | Description                                              |
|---------------|------------|----------------------------------------------------------|
| `--source`    | *requis*   | Chemin vers le dossier contenant les fichiers `.log`     |
| `--niveau`    | `ALL`      | Niveau de filtrage : `ERROR`, `WARN`, `INFO`, `ALL`      |
| `--dest`      | `backups/` | Dossier de destination des archives `.tar.gz`            |
| `--retention` | `30`       | Nombre de jours de rétention des rapports JSON           |

### Exécuter un module individuellement

```bash
# Module analyser seul
python3 analyser.py --source logs_test/ --niveau ERROR

# Module rapport seul (avec des données d'exemple)
python3 rapport.py
```

---

## 4. Description de chaque module

| Fichier          | Auteur   | Rôle                                                                                                       |
|------------------|----------|------------------------------------------------------------------------------------------------------------|
| `main.py`        | Soultone | Point d'entrée — orchestre les 3 modules, gère toutes les erreurs, expose les arguments CLI globaux        |
| `analyser.py`    | Joanita  | Module 1 — scanne les `.log` via `glob`, filtre par niveau, calcule les stats et le Top 5 des erreurs      |
| `rapport.py`     |Féliciano | Module 2 — sérialise les résultats en `rapport_YYYY-MM-DD.json` dans le dossier `rapports/`                |
| `archiver.py`    | Rio      | Module 3 — crée `backup_YYYY-MM-DD.tar.gz`, le déplace via `shutil`, nettoie les rapports obsolètes        |

### Flux de données

```
logs_test/*.log
      │
      ▼
 analyser.py  ──► résultats (dict Python)
      │
      ▼
 rapport.py   ──► rapports/rapport_YYYY-MM-DD.json
      │
      ▼
 archiver.py  ──► backups/backup_YYYY-MM-DD.tar.gz
               ──► suppression des rapports > N jours
```

---

## 5. Planification Cron

Pour exécuter le pipeline **tous les dimanches à 03h00**, ajouter la ligne suivante dans le crontab (`crontab -e`) :

```cron
0 3 * * 0 /usr/bin/python3 /chemin/absolu/loganalyzer/main.py --source /var/logs/app --dest /var/backups/loganalyzer --retention 30 >> /var/log/loganalyzer.log 2>&1
```

Explication champ par champ :

| Champ | Valeur | Signification              |
|-------|--------|----------------------------|
| `0`   | minute | À la minute 0              |
| `3`   | heure  | À 3h du matin              |
| `*`   | jour   | Tous les jours du mois     |
| `*`   | mois   | Tous les mois              |
| `0`   | j.sem. | 0 = dimanche               |

- `>> /var/log/loganalyzer.log 2>&1` redirige stdout et stderr vers un fichier de log persistant.
- Utiliser **chemins absolus** obligatoirement dans le crontab.

---

## 6. Répartition des tâches

| Membre         | Rôle              | Responsabilité principale                                          | Branche Git                  |
|----------------|-------------------|--------------------------------------------------------------------|------------------------------|
| **Soultone**   | Chef de projet    | Init repo, `main.py`, `README.md`, intégration finale, Cron        | `feature/main-readme`        |
| **Joanita**    | Développeur       | `analyser.py` — Module 1 (ingestion, filtrage, statistiques)       | `feature/analyser`           |
| **Féliciano**  | Développeur       | `rapport.py` — Module 2 (génération rapport JSON horodaté)         | `feature/rapport`            |
| **Rio**        | Développeur/Tests | `archiver.py` — Module 3 + données de test `logs_test/`            | `feature/archiver-et-tests`  |

---

## Structure du projet

```
loganalyzer/
├── main.py          # Point d'entrée principal (Soulone)
├── analyser.py      # Module 1 : ingestion et analyse (Joanita)
├── rapport.py       # Module 2 : génération JSON (Féliciano)
├── archiver.py      # Module 3 : archivage et nettoyage (Rio)
├── logs_test/       # Fichiers de logs pour les tests (Rio)
│   ├── app1.log
│   ├── app2.log
│   └── app3.log
├── rapports/        # Généré automatiquement à l'exécution
├── backups/         # Généré automatiquement à l'exécution
└── README.md        # Cette documentation (Soultone)
```
