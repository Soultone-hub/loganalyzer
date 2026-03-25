#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module 3 — Archivage et Nettoyage
Auteur    : Diana
Branche   : feature/archiver-et-tests
Rôle      : Créer une archive .tar.gz des logs traités, la déplacer vers le
            dossier de destination, puis supprimer les rapports JSON obsolètes
            selon la politique de rétention.
"""

import os
import shutil
import subprocess
import tarfile
import time
from datetime import datetime


# Dossier backups par défaut, défini relativement à ce fichier
DOSSIER_BACKUPS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
DOSSIER_RAPPORTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapports")


def s_assurer_dossier_dest(dossier_dest):
    """
    Crée le dossier de destination s'il n'existe pas.

    Args:
        dossier_dest (str): Chemin absolu vers le dossier cible.

    Returns:
        str: Chemin absolu créé/existant.
    """
    chemin = os.path.abspath(dossier_dest)
    os.makedirs(chemin, exist_ok=True)
    return chemin


def verifier_espace_disque(dossier_dest, seuil_mo=50):
    """
    Vérifie l'espace disque disponible dans le dossier de destination via subprocess.

    La commande utilisée est 'df -BM <dossier>' sur Linux/macOS,
    et 'wmic logicaldisk' sur Windows.

    Args:
        dossier_dest (str): Chemin du dossier de destination.
        seuil_mo     (int): Espace minimum requis en Mo (défaut : 50 Mo).

    Returns:
        bool: True si l'espace est suffisant, False sinon.

    Raises:
        RuntimeError: Si la commande système échoue.
    """
    try:
        if os.name == "nt":   # Windows
            disque = os.path.splitdrive(os.path.abspath(dossier_dest))[0]
            cmd = ["wmic", "logicaldisk", f"where", f"DeviceID='{disque}'",
                   "get", "FreeSpace", "/value"]
            sortie = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            for ligne in sortie.splitlines():
                if "FreeSpace=" in ligne:
                    libre_octets = int(ligne.split("=")[1].strip())
                    libre_mo = libre_octets / (1024 * 1024)
                    print(f"[archiver] Espace disque libre     : {libre_mo:.0f} Mo")
                    return libre_mo >= seuil_mo
        else:                 # Linux / macOS
            cmd = ["df", "-BM", dossier_dest]
            sortie = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            lignes = sortie.strip().splitlines()
            if len(lignes) >= 2:
                colonnes = lignes[1].split()
                libre_mo = int(colonnes[3].replace("M", ""))
                print(f"[archiver] Espace disque libre     : {libre_mo} Mo")
                return libre_mo >= seuil_mo
    except (subprocess.CalledProcessError, IndexError, ValueError) as e:
        raise RuntimeError(f"Impossible de vérifier l'espace disque : {e}")

    return True   # Par défaut on laisse passer si la détection échoue


def creer_archive(fichiers_log, dossier_dest):
    """
    Archive les fichiers .log traités dans un fichier backup_YYYY-MM-DD.tar.gz
    et le dépose dans le dossier de destination.

    Args:
        fichiers_log (list[str]): Chemins absolus vers les fichiers .log à archiver.
        dossier_dest (str)      : Chemin absolu du dossier de destination.

    Returns:
        str: Chemin absolu de l'archive créée dans dossier_dest.

    Raises:
        FileNotFoundError: Si un fichier log est introuvable.
        OSError: En cas d'erreur lors de la création de l'archive.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    nom_archive = f"backup_{date_str}.tar.gz"

    # Créer l'archive dans un répertoire temporaire (dossier du script)
    tmp = os.path.dirname(os.path.abspath(__file__))
    chemin_tmp = os.path.join(tmp, nom_archive)

    with tarfile.open(chemin_tmp, "w:gz") as tar:
        for fichier in fichiers_log:
            if not os.path.isfile(fichier):
                raise FileNotFoundError(f"Fichier log introuvable : '{fichier}'")
            tar.add(fichier, arcname=os.path.basename(fichier))

    # Déplacer l'archive vers le dossier de destination
    dest = s_assurer_dossier_dest(dossier_dest)
    chemin_final = os.path.join(dest, nom_archive)
    shutil.move(chemin_tmp, chemin_final)

    print(f"[archiver] Archive créée           : {chemin_final}")
    return chemin_final


def nettoyer_anciens_rapports(dossier_rapports=None, retention_jours=30):
    """
    Supprime les fichiers rapport_*.json dont l'âge dépasse la politique de rétention.

    L'âge est calculé via os.path.getmtime() et time.time().

    Args:
        dossier_rapports (str|None): Chemin absolu vers le dossier des rapports.
                                     Si None, utilise le dossier 'rapports/' du projet.
        retention_jours  (int)     : Nombre de jours de rétention (défaut : 30).

    Returns:
        list[str]: Liste des fichiers supprimés.
    """
    if dossier_rapports is None:
        dossier_rapports = DOSSIER_RAPPORTS

    if not os.path.isdir(dossier_rapports):
        print(f"[archiver] Dossier rapports absent, nettoyage ignoré.")
        return []

    maintenant = time.time()
    seuil_secondes = retention_jours * 86400   # 86400 s = 1 jour
    supprimes = []

    for nom in os.listdir(dossier_rapports):
        if not nom.startswith("rapport_") or not nom.endswith(".json"):
            continue

        chemin = os.path.join(dossier_rapports, nom)
        age_secondes = maintenant - os.path.getmtime(chemin)

        if age_secondes > seuil_secondes:
            os.remove(chemin)
            supprimes.append(chemin)
            print(f"[archiver] Rapport supprimé        : {chemin}")

    if not supprimes:
        print(f"[archiver] Aucun rapport obsolète (rétention : {retention_jours} j).")

    return supprimes


def archiver_et_nettoyer(fichiers_log, dossier_dest=None, retention_jours=30):
    """
    Point d'entrée du module : vérifie l'espace disque, crée l'archive
    et nettoie les anciens rapports.

    Args:
        fichiers_log    (list[str]): Chemins vers les fichiers .log à archiver.
        dossier_dest    (str|None) : Dossier de destination de l'archive.
        retention_jours (int)      : Politique de rétention en jours.

    Returns:
        str: Chemin de l'archive créée.

    Raises:
        RuntimeError: Si l'espace disque est insuffisant.
    """
    if dossier_dest is None:
        dossier_dest = DOSSIER_BACKUPS

    chemin_dest = s_assurer_dossier_dest(dossier_dest)

    # Vérification espace disque
    if not verifier_espace_disque(chemin_dest):
        raise RuntimeError(
            f"Espace disque insuffisant dans '{chemin_dest}' (seuil : 50 Mo)."
        )

    # Archivage
    chemin_archive = creer_archive(fichiers_log, chemin_dest)

    # Nettoyage
    nettoyer_anciens_rapports(retention_jours=retention_jours)

    return chemin_archive
