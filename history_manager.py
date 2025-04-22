# -*- coding: utf-8 -*-
# history_manager.py : Gestion de l'historique des commandes pour Luciole

import os
import readline
import atexit
# Importe les couleurs pour _save_history et Console pour setup_history
from config import HISTFILE, HISTSIZE, COLOR_YELLOW, COLOR_RED, COLOR_RESET
from rich.console import Console # <--- Import ajouté

def _save_history():
    """Fonction interne pour sauvegarder l'historique."""
    # On garde print standard ici car appelé par atexit
    try:
        readline.write_history_file(HISTFILE)
    except Exception as e:
        # Utilise les codes ANSI bruts ici
        print(f"{COLOR_RED}Avertissement: Impossible de sauvegarder l'historique dans {HISTFILE}: {e}{COLOR_RESET}")

# --- MODIFICATION : setup_history accepte et utilise l'objet console ---
def setup_history(console: Console):
    """Charge l'historique existant et enregistre la sauvegarde à la sortie."""
    try:
        # Utilise console.print avec markup Rich
        console.print(f"[yellow]Chargement de l'historique depuis {HISTFILE}[/yellow]")
        readline.read_history_file(HISTFILE)
        readline.set_history_length(HISTSIZE)
    except FileNotFoundError:
        # Utilise console.print avec markup Rich
        console.print(f"[yellow]Fichier d'historique non trouvé (sera créé à la sortie).[/yellow]")
    except Exception as e:
        # Utilise console.print avec markup Rich
        console.print(f"[red]Avertissement: Impossible de charger l'historique: {e}[/red]")

    # Enregistre la fonction de sauvegarde (inchangé)
    atexit.register(_save_history)
# --- FIN MODIFICATION ---

# Fonction add_history_entry inchangée (n'affiche rien)
def add_history_entry(entry):
    """Ajoute une entrée à l'historique en mémoire."""
    if entry: # N'ajoute pas d'entrées vides
        readline.add_history(entry)