#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module 4 — Point d'entrée et Orchestration
Auteur    : Alice (Chef de projet)
Branche   : feature/main-readme
Rôle      : Appelle les 3 modules dans l'ordre correct, gère toutes les erreurs
            et expose les arguments CLI globaux.

Utilisation :
    python main.py --source /chemin/logs --niveau ERROR --dest /chemin/backups --retention 30

Planification Cron (tous les dimanches à 03h00) :
    0 3 * * 0 /usr/bin/python3 /chemin/absolu/loganalyzer/main.py \
              --source /var/logs/app --dest /var/backups/loganalyzer >> /var/log/loganalyzer.log 2>&1
"""

import argparse
import os
import sys

# ── Tous les chemins sont absolus, construits depuis __file__ ──────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import analyser
import rapport
import archiver


def parser_arguments():
    """
    Définit et retourne les arguments CLI de l'orchestrateur.

    Arguments :
        --source     Dossier contenant les fichiers .log  (obligatoire)
        --niveau     Niveau de filtrage : ERROR/WARN/INFO/ALL  (défaut : ALL)
        --dest       Dossier de destination des archives  (défaut : backups/)
        --retention  Nombre de jours de rétention des rapports  (défaut : 30)
    """
    parser = argparse.ArgumentParser(
        description="LogAnalyzer Pro — Pipeline d'analyse et d'archivage de logs"
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Chemin vers le dossier contenant les fichiers .log"
    )
    parser.add_argument(
        "--niveau",
        default="ALL",
        choices=("ERROR", "WARN", "INFO", "ALL"),
        help="Niveau de filtrage des logs (défaut : ALL)"
    )
    parser.add_argument(
        "--dest",
        default=os.path.join(BASE_DIR, "backups"),
        help="Dossier de destination des archives .tar.gz (défaut : backups/)"
    )
    parser.add_argument(
        "--retention",
        type=int,
        default=30,
        help="Nombre de jours de rétention des rapports JSON (défaut : 30)"
    )
    return parser.parse_args()


def main():
    """
    Orchestre l'exécution du pipeline complet :
        1. Analyse des logs (analyser.py)
        2. Génération du rapport JSON (rapport.py)
        3. Archivage des logs + nettoyage des anciens rapports (archiver.py)

    Toute erreur fatale provoque un sys.exit(1) avec un message explicite.
    """
    args = parser_arguments()
    dossier_source = os.path.abspath(args.source)
    dossier_dest   = os.path.abspath(args.dest)

    print("=" * 60)
    print("  LogAnalyzer Pro — Démarrage du pipeline")
    print("=" * 60)
    print(f"  Source     : {dossier_source}")
    print(f"  Niveau     : {args.niveau}")
    print(f"  Dest       : {dossier_dest}")
    print(f"  Rétention  : {args.retention} jours")
    print("=" * 60)

    # ── Étape 1 : Analyse ────────────────────────────────────────────────────
    print("\n[ÉTAPE 1] Ingestion et analyse des logs...")
    try:
        resultats = analyser.analyser_tous(dossier_source, args.niveau)
    except FileNotFoundError as e:
        print(f"[ERREUR] Analyse impossible : {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue durant l'analyse : {e}", file=sys.stderr)
        sys.exit(1)

    # ── Étape 2 : Rapport JSON ───────────────────────────────────────────────
    print("\n[ÉTAPE 2] Génération du rapport JSON...")
    try:
        chemin_rapport = rapport.generer_rapport(resultats)
    except OSError as e:
        print(f"[ERREUR] Impossible d'écrire le rapport : {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue lors de la génération du rapport : {e}",
              file=sys.stderr)
        sys.exit(1)

    # ── Étape 3 : Archivage + nettoyage ─────────────────────────────────────
    print("\n[ÉTAPE 3] Archivage des fichiers traités et nettoyage...")
    try:
        fichiers_log = resultats["fichiers_traites"]
        archiver.archiver_et_nettoyer(
            fichiers_log,
            dossier_dest=dossier_dest,
            retention_jours=args.retention
        )
    except FileNotFoundError as e:
        print(f"[ERREUR] Fichier introuvable lors de l'archivage : {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"[ERREUR] Archivage impossible : {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue lors de l'archivage : {e}", file=sys.stderr)
        sys.exit(1)

    # ── Résumé final ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Pipeline terminé avec succès.")
    print(f"  Rapport JSON   : {chemin_rapport}")
    print(f"  Archives       : {dossier_dest}")
    print("=" * 60)


if __name__ == "__main__":
    main()
