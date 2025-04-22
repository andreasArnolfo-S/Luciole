#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main.py : Point d'entrée principal pour Foxi v5 (structuré)

import os
import sys
from collections import deque # <--- Pour l'historique de contexte

# Importer les modules du projet
import config as cfg
from history_manager import setup_history, add_history_entry
from shell_utils import execute_command, change_directory
from ollama_client import get_ollama_analysis, get_command_from_natural_language

# (Les fonctions print_result, print_analysis, is_dangerous, print_help_message restent inchangées)
def print_result(stdout, stderr):
    print(f"\n{cfg.COLOR_CYAN}--- Résultat Brut ---{cfg.COLOR_RESET}")
    has_output = False
    if stdout is not None and stdout.strip():
        print(f"{cfg.COLOR_GREEN}Sortie standard:{cfg.COLOR_RESET}\n{stdout.strip()}")
        has_output = True
    if stderr is not None and stderr.strip():
        print(f"{cfg.COLOR_RED}Sortie d'erreur:{cfg.COLOR_RESET}\n{stderr.strip()}")
        has_output = True
    if not has_output:
        print("(Aucune sortie notable)")
    print(f"{cfg.COLOR_CYAN}--------------------{cfg.COLOR_RESET}")

def print_analysis(analysis_result):
    print(f"\n{cfg.COLOR_CYAN}--- Analyse Foxi ---{cfg.COLOR_RESET}")
    if analysis_result:
        print(analysis_result) # analysis_result peut contenir une erreur formatée ou rien si stream OK
    print(f"{cfg.COLOR_CYAN}--------------------{cfg.COLOR_RESET}")

def is_dangerous(command):
    return any(keyword in command for keyword in cfg.DANGEROUS_KEYWORDS)

def print_help_message():
    """Affiche le message d'aide formaté."""
    print(f"\n{cfg.COLOR_BOLD}{cfg.COLOR_CYAN}--- Aide Foxi ---{cfg.COLOR_RESET}")
    print(f"Foxi est un assistant de terminal utilisant Ollama pour analyser")
    print(f"les commandes ou traduire le langage naturel en commandes shell.")
    print(f"\n{cfg.COLOR_BOLD}Modes d'Opération :{cfg.COLOR_RESET}")
    print(f"  {cfg.COLOR_GREEN}commande{cfg.COLOR_RESET} : Exécute directement les commandes shell entrées.")
    print(f"           Foxi analyse ensuite la sortie.")
    print(f"  {cfg.COLOR_MAGENTA}naturel {cfg.COLOR_RESET} : Vous écrivez une demande en français.")
    print(f"           Foxi la traduit en commande, vous la montre, puis")
    print(f"           l'exécute et analyse le résultat.")
    print(f"\n{cfg.COLOR_BOLD}Commandes Spéciales :{cfg.COLOR_RESET}")
    print(f"  {cfg.COLOR_YELLOW}/mode{cfg.COLOR_RESET}    : Permet de basculer entre le mode 'commande' et 'naturel'.")
    print(f"  {cfg.COLOR_YELLOW}/help{cfg.COLOR_RESET}    : Affiche ce message d'aide.")
    print(f"  {cfg.COLOR_YELLOW}quitter{cfg.COLOR_RESET} : Quitte l'application Foxi.")
    print(f"\n{cfg.COLOR_BOLD}Navigation :{cfg.COLOR_RESET}")
    print(f"  Flèches {cfg.COLOR_BOLD}Haut{cfg.COLOR_RESET}/{cfg.COLOR_BOLD}Bas{cfg.COLOR_RESET} : Navigue dans l'historique des commandes saisies.")
    print(f"{cfg.COLOR_BOLD}{cfg.COLOR_CYAN}-----------------{cfg.COLOR_RESET}")


def main():
    # Initialisation (accueil, historique readline, choix modèle)
    print(f"{cfg.COLOR_BOLD}{cfg.COLOR_BLUE}Bienvenue dans l'outil de commande assisté Foxi v5 !{cfg.COLOR_RESET}")
    print(f"{cfg.COLOR_YELLOW}Assurez-vous qu'Ollama est lancé (ex: 'ollama run {cfg.DEFAULT_MODEL}').{cfg.COLOR_RESET}")
    setup_history()
    model_input = input(f"{cfg.COLOR_GREEN}Quel modèle Ollama utiliser ? [Défaut: {cfg.DEFAULT_MODEL}] > {cfg.COLOR_RESET}").strip()
    model_to_use = model_input if model_input else cfg.DEFAULT_MODEL
    print(f"{cfg.COLOR_YELLOW}Utilisation du modèle : {model_to_use}{cfg.COLOR_RESET}")
    current_mode = "commande"
    print(f"\n{cfg.COLOR_GREEN}Mode actuel : {current_mode}. Tapez '/mode' pour changer.{cfg.COLOR_RESET}")
    print(f"{cfg.COLOR_GREEN}Utilisez les flèches Haut/Bas pour l'historique. Tapez 'quitter' pour arrêter.{cfg.COLOR_RESET}")

    # Initialisation de l'historique de conversation (contexte)
    conversation_history = deque(maxlen=3) # Garde les 3 dernières interactions

    while True:
        try:
            # Affichage du prompt
            current_dir_short = os.path.basename(os.getcwd())
            prompt_color = cfg.COLOR_GREEN if current_mode == "commande" else cfg.COLOR_MAGENTA
            prompt_indicator = "Commande >" if current_mode == "commande" else "Parlez >"
            prompt_text = (f"\n{cfg.COLOR_CYAN}({current_dir_short}) "
                           f"{cfg.COLOR_RESET}{cfg.COLOR_BOLD}{prompt_color}"
                           f"{prompt_indicator} {cfg.COLOR_RESET}")
            user_input = input(prompt_text).strip()

            # Commandes internes et gestion historique readline
            if user_input.lower() == 'quitter': break
            if not user_input: continue
            add_history_entry(user_input) # Ajout à l'historique readline

            if user_input.lower() == "/help":
                print_help_message()
                continue
            if user_input == "/mode":
                current_mode = "naturel" if current_mode == "commande" else "commande"
                print(f"{cfg.COLOR_YELLOW}Passage en mode : {current_mode}{cfg.COLOR_RESET}")
                continue

            # --- Logique par Mode ---
            executed_command = None
            stdout, stderr = None, None

            if current_mode == "naturel":
                # Appel à Ollama pour traduction (passe maintenant l'historique)
                generated_command = get_command_from_natural_language(
                    user_input, model_to_use,
                    conversation_history=conversation_history # <-- Argument ajouté
                )
                if generated_command:
                    print(f"{cfg.COLOR_YELLOW}Commande suggérée : {generated_command}{cfg.COLOR_RESET}")
                    execute_it = True
                    if is_dangerous(generated_command):
                         confirm = input(f"{cfg.COLOR_BOLD}{cfg.COLOR_RED}ATTENTION : Commande potentiellement dangereuse ! Exécuter '{generated_command}' ? (o/N) > {cfg.COLOR_RESET}").lower()
                         if confirm != 'o':
                            print(f"{cfg.COLOR_YELLOW}Exécution annulée.{cfg.COLOR_RESET}")
                            execute_it = False
                    if execute_it:
                        # Exécution et récupération sortie
                        executed_command = generated_command
                        stdout, stderr = execute_command(executed_command)
                        print_result(stdout, stderr)
                        # L'analyse se fera dans le bloc commun ci-dessous
                else:
                    print(f"{cfg.COLOR_RED}Impossible de générer une commande pour cette demande.{cfg.COLOR_RESET}")

            elif current_mode == "commande":
                command_to_run = user_input
                # Gérer 'cd' qui n'est pas historisé/analysé
                if command_to_run.startswith("cd ") or command_to_run == "cd":
                    parts = command_to_run.split(maxsplit=1)
                    target_dir = parts[1] if len(parts) > 1 else "~"
                    change_directory(target_dir)
                    continue

                # Exécution et récupération sortie
                executed_command = command_to_run
                stdout, stderr = execute_command(executed_command)
                print_result(stdout, stderr)
                # L'analyse se fera dans le bloc commun ci-dessous

            # --- Mise à jour historique contexte ET Analyse (si une commande a été exécutée) ---
            if executed_command is not None:
                # Ajoute l'interaction à l'historique de contexte
                conversation_history.append((executed_command, stdout, stderr))

                # Logique d'analyse (directe ou via Ollama avec contexte)
                is_successful = stderr is None or not stderr.strip()
                use_ollama = True
                direct_analysis_output = None

                if is_successful: # Analyse directe uniquement si succès
                    if executed_command in cfg.SIMPLE_COMMANDS:
                         if executed_command == "pwd": direct_analysis_output = f"{cfg.COLOR_BLUE}Vous êtes actuellement dans le dossier : {stdout.strip()}{cfg.COLOR_RESET}"
                         elif executed_command == "whoami": direct_analysis_output = f"{cfg.COLOR_BLUE}Vous êtes connecté en tant que : {stdout.strip()}{cfg.COLOR_RESET}"
                         use_ollama = False
                    elif cfg.ECHO_XXD_PIPE in executed_command:
                         direct_analysis_output = f"{cfg.COLOR_BLUE}Le résultat décodé (echo | xxd -r -p) est :\n{stdout.strip()}{cfg.COLOR_RESET}"
                         use_ollama = False

                if use_ollama:
                    prompt_type = "detailed"
                    # Utiliser le prompt simple pour 'ls' réussi
                    if (executed_command == cfg.LS_COMMAND or executed_command.startswith(cfg.LS_COMMAND + " ")) and is_successful:
                         prompt_type = "simple_ls"

                    # Appel à Ollama pour analyse (passe maintenant l'historique)
                    analysis_result = get_ollama_analysis(
                        executed_command, stdout, stderr, model_to_use, prompt_type=prompt_type,
                        conversation_history=conversation_history # <-- Argument ajouté
                    )
                    print_analysis(analysis_result) # Gère l'affichage (stream ou erreur)
                else:
                    # Afficher l'analyse directe
                    print_analysis(direct_analysis_output)

        except KeyboardInterrupt:
            print(f"\n{cfg.COLOR_YELLOW}Interruption reçue. Sauvegarde de l'historique et sortie...{cfg.COLOR_RESET}")
            break
        except Exception as e:
            # Log l'erreur complète pour le débogage si nécessaire
            # import traceback
            # traceback.print_exc()
            print(f"\n{cfg.COLOR_RED}{cfg.COLOR_BOLD}Une erreur critique est survenue dans la boucle principale:{cfg.COLOR_RESET}")
            print(f"{cfg.COLOR_RED}{type(e).__name__}: {e}{cfg.COLOR_RESET}")
            print(f"{cfg.COLOR_YELLOW}Tentative de continuation...{cfg.COLOR_RESET}")

    print(f"\n{cfg.COLOR_BOLD}{cfg.COLOR_BLUE}Foxi terminé. Au revoir !{cfg.COLOR_RESET}")

if __name__ == "__main__":
    main()