# -*- coding: utf-8 -*-
# history_manager.py : Gestion de l'historique des commandes pour Foxi

import os
import readline
import atexit
from config import HISTFILE, HISTSIZE, COLOR_YELLOW, COLOR_RED, COLOR_RESET

def _save_history():
    """Fonction interne pour sauvegarder l'historique."""
    try:
        readline.write_history_file(HISTFILE)
    except Exception as e:
        print(f"{COLOR_RED}Avertissement: Impossible de sauvegarder l'historique dans {HISTFILE}: {e}{COLOR_RESET}")

def setup_history():
    """Charge l'historique existant et enregistre la sauvegarde à la sortie."""
    try:
        print(f"{COLOR_YELLOW}Chargement de l'historique depuis {HISTFILE}{COLOR_RESET}")
        readline.read_history_file(HISTFILE)
        readline.set_history_length(HISTSIZE)
    except FileNotFoundError:
        print(f"{COLOR_YELLOW}Fichier d'historique non trouvé (sera créé à la sortie).{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Avertissement: Impossible de charger l'historique: {e}{COLOR_RESET}")

    # Enregistre la fonction de sauvegarde pour qu'elle soit appelée à la sortie du script
    atexit.register(_save_history)

def add_history_entry(entry):
    """Ajoute une entrée à l'historique en mémoire."""
    if entry: # N'ajoute pas d'entrées vides
        readline.add_history(entry)
