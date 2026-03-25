#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import os
from datetime import datetime


DOSSIER_RAPPORTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapports")


def s_assurer_dossier_rapports():
    
    os.makedirs(DOSSIER_RAPPORTS, exist_ok=True)
    return DOSSIER_RAPPORTS


def construire_structure_rapport(resultats_analyse):
    
    maintenant = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta = resultats_analyse.get("metadata", {})
    stats = resultats_analyse.get("statistiques", {})

    rapport = {
        "metadata": {
            "date": maintenant,
            "utilisateur": meta.get("utilisateur", "inconnu"),
            "os": meta.get("os", "inconnu"),
            "source": meta.get("source", "")
        },
        "statistiques": {
            "total_lignes": stats.get("total_lignes", 0),
            "par_niveau": stats.get("par_niveau", {"ERROR": 0, "WARN": 0, "INFO": 0}),
            "top5_erreurs": stats.get("top5_erreurs", [])
        },
        "fichiers_traites": resultats_analyse.get("fichiers_traites", [])
    }

    return rapport


def generer_nom_fichier():
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"rapport_{date_str}.json"


def ecrire_rapport(rapport_dict):
    
    dossier = s_assurer_dossier_rapports()
    nom_fichier = generer_nom_fichier()
    chemin_rapport = os.path.join(dossier, nom_fichier)

    with open(chemin_rapport, "w", encoding="utf-8") as f:
        json.dump(rapport_dict, f, ensure_ascii=False, indent=4)

    return chemin_rapport


def generer_rapport(resultats_analyse):
    
    rapport_dict = construire_structure_rapport(resultats_analyse)
    chemin = ecrire_rapport(rapport_dict)
    print(f"[rapport] Rapport généré           : {chemin}")
    return chemin


if __name__ == "__main__":
    exemple = {
        "metadata": {
            "os": "Linux 5.15",
            "utilisateur": "charlie",
            "source": "/tmp/logs_test"
        },
        "statistiques": {
            "total_lignes": 60,
            "par_niveau": {"ERROR": 10, "WARN": 15, "INFO": 35},
            "top5_erreurs": [
                {"message": "Connexion refusée", "occurrences": 4},
                {"message": "Timeout LDAP", "occurrences": 3}
            ]
        },
        "fichiers_traites": ["/tmp/logs_test/app1.log", "/tmp/logs_test/app2.log"]
    }
    generer_rapport(exemple)