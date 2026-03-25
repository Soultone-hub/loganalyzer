
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import glob
import os
import platform
from collections import Counter

NIVEAUX_VALIDES = ("ERROR", "WARN", "INFO", "ALL")


def parser_arguments():
    """Définit et retourne les arguments CLI du module analyser."""
    parser = argparse.ArgumentParser(
        description="LogAnalyzer Pro — Module d'ingestion et d'analyse"
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Chemin vers le dossier contenant les fichiers .log (obligatoire)"
    )
    parser.add_argument(
        "--niveau",
        default="ALL",
        choices=NIVEAUX_VALIDES,
        help="Niveau de filtrage : ERROR, WARN, INFO ou ALL (défaut : ALL)"
    )
    return parser.parse_args()


def scanner_fichiers_log(dossier_source):
    """
    Scanne le dossier source et retourne la liste des fichiers .log trouvés.

    Args:
        dossier_source (str): Chemin absolu vers le dossier à scanner.

    Returns:
        list[str]: Liste des chemins absolus vers les fichiers .log.

    Raises:
        FileNotFoundError: Si le dossier source n'existe pas.
    """
    if not os.path.isdir(dossier_source):
        raise FileNotFoundError(f"Le dossier source '{dossier_source}' est introuvable.")

    pattern = os.path.join(os.path.abspath(dossier_source), "*.log")
    fichiers = glob.glob(pattern)

    if not fichiers:
        raise FileNotFoundError(f"Aucun fichier .log trouvé dans '{dossier_source}'.")

    return fichiers


def analyser_fichier(chemin_fichier, niveau_filtre="ALL"):
    """
    Lit un fichier .log ligne par ligne et filtre selon le niveau demandé.

    Format attendu : YYYY-MM-DD HH:MM:SS NIVEAU Message

    Args:
        chemin_fichier (str): Chemin absolu vers le fichier .log.
        niveau_filtre  (str): Niveau de filtrage (ERROR, WARN, INFO, ALL).

    Returns:
        dict: {
            "lignes_totales": int,
            "lignes_filtrees": list[str],
            "comptage": {"ERROR": int, "WARN": int, "INFO": int}
        }
    """
    comptage = {"ERROR": 0, "WARN": 0, "INFO": 0}
    lignes_filtrees = []
    total = 0

    with open(chemin_fichier, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.rstrip("\n")
            if not ligne.strip():
                continue

            total += 1
            parties = ligne.split(" ", 3)   # [date, heure, niveau, message]

            if len(parties) < 4:
                continue

            niv = parties[2].upper()

            # Comptage tous niveaux
            if niv in comptage:
                comptage[niv] += 1
 # Filtrage
            if niveau_filtre == "ALL" or niv == niveau_filtre:
                lignes_filtrees.append(ligne)

    return {
        "lignes_totales": total,
        "lignes_filtrees": lignes_filtrees,
        "comptage": comptage
    }


def calculer_top5_erreurs(lignes_filtrees):
    """
    Extrait le Top 5 des messages ERROR les plus fréquents.

    Args:
        lignes_filtrees (list[str]): Lignes déjà filtrées par analyser_fichier.

    Returns:
        list[tuple]: Paires (message, occurrences) triées par fréquence décroissante.
    """
    messages_error = []

    for ligne in lignes_filtrees:
        parties = ligne.split(" ", 3)
        if len(parties) >= 4 and parties[2].upper() == "ERROR":
            messages_error.append(parties[3])

    compteur = Counter(messages_error)
    return compteur.most_common(5)


def obtenir_metadonnees(dossier_source):
    """
    Collecte les métadonnées système : OS, utilisateur, chemin source.

    Args:
        dossier_source (str): Chemin du dossier analysé.

    Returns:
        dict: {"os": str, "utilisateur": str, "source": str}
    """
    return {
        "os": platform.system() + " " + platform.release(),
        "utilisateur": os.environ.get("USERNAME") or os.environ.get("USER", "inconnu"),
        "source": os.path.abspath(dossier_source)
    }


def analyser_tous(dossier_source, niveau_filtre="ALL"):
    """
    Orchestre l'analyse complète : scan, filtrage, stats, métadonnées.

    Args:
        dossier_source (str): Chemin vers le dossier de logs.
        niveau_filtre  (str): Niveau de filtrage.

    Returns:
        dict: Résultat global contenant les statistiques, les fichiers et les métadonnées.
    """
    fichiers = scanner_fichiers_log(dossier_source)

    total_lignes = 0
    comptage_global = {"ERROR": 0, "WARN": 0, "INFO": 0}
    toutes_lignes_filtrees = []

    for fichier in fichiers:
        resultat = analyser_fichier(fichier, niveau_filtre)
        total_lignes += resultat["lignes_totales"]

        for niv in comptage_global:
            comptage_global[niv] += resultat["comptage"][niv]

        toutes_lignes_filtrees.extend(resultat["lignes_filtrees"])

    top5 = calculer_top5_erreurs(toutes_lignes_filtrees)
    meta = obtenir_metadonnees(dossier_source)

    return {
        "metadata": meta,
        "statistiques": {
            "total_lignes": total_lignes,
            "par_niveau": comptage_global,
            "top5_erreurs": [{"message": msg, "occurrences": n} for msg, n in top5]
        },
        "fichiers_traites": [os.path.abspath(f) for f in fichiers]
    }


if __name__ == "__main__":
    args = parser_arguments()
    resultats = analyser_tous(args.source, args.niveau)

    print(f"[analyser] Fichiers traités       : {len(resultats['fichiers_traites'])}")
    print(f"[analyser] Lignes totales          : {resultats['statistiques']['total_lignes']}")
    print(f"[analyser] Comptage par niveau     : {resultats['statistiques']['par_niveau']}")
    print(f"[analyser] Top 5 erreurs           :")
    for e in resultats["statistiques"]["top5_erreurs"]:
        print(f"            {e['occurrences']}x — {e['message']}")

