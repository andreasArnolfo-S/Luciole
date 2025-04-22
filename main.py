#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main.py : Point d'entrée principal pour Luciole v5 (structuré)

import os
import sys
from collections import deque # Pour l'historique de contexte

# Importer les modules du projet
import config as cfg
# Assure-toi que config.py contient la liste cfg.SECURITY_TOOLS
from history_manager import setup_history, add_history_entry
from shell_utils import execute_command, change_directory
# Importe la nouvelle fonction avec les autres
from ollama_client import get_ollama_analysis, get_command_from_natural_language, get_tool_suggestions

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
    print(f"\n{cfg.COLOR_CYAN}--- Analyse Luciole ---{cfg.COLOR_RESET}")
    if analysis_result:
        print(analysis_result) # analysis_result peut contenir une erreur formatée ou rien si stream OK
    print(f"{cfg.COLOR_CYAN}--------------------{cfg.COLOR_RESET}")

def is_dangerous(command):
    return any(keyword in command for keyword in cfg.DANGEROUS_KEYWORDS)

def print_help_message():
    """Affiche le message d'aide formaté."""
    print(f"\n{cfg.COLOR_BOLD}{cfg.COLOR_CYAN}--- Aide Luciole ---{cfg.COLOR_RESET}")
    print(f"Luciole est un assistant de terminal utilisant Ollama pour analyser")
    print(f"les commandes ou traduire le langage naturel en commandes shell.")
    print(f"Il peut aussi suggérer des outils avec /suggest_tools [description].") # Ajout info aide
    print(f"\n{cfg.COLOR_BOLD}Modes d'Opération :{cfg.COLOR_RESET}")
    print(f"  {cfg.COLOR_GREEN}commande{cfg.COLOR_RESET} : Exécute directement les commandes shell entrées.")
    print(f"           Luciole analyse ensuite la sortie.")
    print(f"  {cfg.COLOR_MAGENTA}naturel {cfg.COLOR_RESET} : Vous écrivez une demande en français.")
    print(f"           Luciole la traduit en commande, vous la montre, puis")
    print(f"           l'exécute et analyse le résultat.")
    print(f"\n{cfg.COLOR_BOLD}Commandes Spéciales :{cfg.COLOR_RESET}")
    print(f"  {cfg.COLOR_YELLOW}/mode{cfg.COLOR_RESET}           : Permet de basculer entre le mode 'commande' et 'naturel'.")
    print(f"  {cfg.COLOR_YELLOW}/help{cfg.COLOR_RESET}           : Affiche ce message d'aide.")
    print(f"  {cfg.COLOR_YELLOW}/suggest_tools ...{cfg.COLOR_RESET}: Suggère des outils pour la tâche décrite.") # Ajout info aide
    print(f"  {cfg.COLOR_YELLOW}quitter{cfg.COLOR_RESET}        : Quitte l'application Luciole.")
    print(f"\n{cfg.COLOR_BOLD}Navigation :{cfg.COLOR_RESET}")
    print(f"  Flèches {cfg.COLOR_BOLD}Haut{cfg.COLOR_RESET}/{cfg.COLOR_BOLD}Bas{cfg.COLOR_RESET} : Navigue dans l'historique des commandes saisies.")
    print(f"{cfg.COLOR_BOLD}{cfg.COLOR_CYAN}-----------------{cfg.COLOR_RESET}")


def main():
    # Initialisation (accueil, historique readline, choix modèle)
    print(f"{cfg.COLOR_BOLD}{cfg.COLOR_BLUE}Bienvenue dans l'outil de commande assisté Luciole v5 !{cfg.COLOR_RESET}")
    print(f"{cfg.COLOR_YELLOW}Assurez-vous qu'Ollama est lancé (ex: 'ollama run {cfg.DEFAULT_MODEL}').{cfg.COLOR_RESET}")
    setup_history()
    model_input = input(f"{cfg.COLOR_GREEN}Quel modèle Ollama utiliser ? [Défaut: {cfg.DEFAULT_MODEL}] > {cfg.COLOR_RESET}").strip()
    model_to_use = model_input if model_input else cfg.DEFAULT_MODEL
    print(f"{cfg.COLOR_YELLOW}Utilisation du modèle : {model_to_use}{cfg.COLOR_RESET}")
    current_mode = "commande"
    print(f"\n{cfg.COLOR_GREEN}Mode actuel : {current_mode}. Tapez '/mode' pour changer.{cfg.COLOR_RESET}")
    print(f"{cfg.COLOR_GREEN}Commandes spéciales: /help, /suggest_tools [tâche], quitter{cfg.COLOR_RESET}") # Info rapide

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

            # --- NOUVEAU : Gérer /suggest_tools ---
            elif user_input.lower().startswith("/suggest_tools "):
                task_description = user_input[len("/suggest_tools "):].strip()
                if not task_description:
                    print(f"{cfg.COLOR_YELLOW}Veuillez décrire la tâche après /suggest_tools. Exemple : /suggest_tools scanner des ports{cfg.COLOR_RESET}")
                    continue

                print(f"\n{cfg.COLOR_YELLOW}Recherche d'outils pour : \"{task_description}\"{cfg.COLOR_RESET}")
                suggestions = get_tool_suggestions(task_description, model_to_use) # Appel de la nouvelle fonction client

                # Afficher les suggestions
                print(f"\n{cfg.COLOR_CYAN}--- Suggestions d'Outils ---{cfg.COLOR_RESET}")
                if suggestions:
                    if not suggestions.strip().startswith(cfg.COLOR_RED):
                         print(f"{cfg.COLOR_BLUE}{suggestions}{cfg.COLOR_RESET}")
                    else:
                         print(suggestions) # Afficher tel quel si c'est une erreur colorée
                else:
                    print("(Aucune suggestion générée ou erreur lors de la requête.)")
                print(f"{cfg.COLOR_CYAN}---------------------------{cfg.COLOR_RESET}")

                continue # Revenir au prompt après avoir affiché les suggestions
            # --- FIN NOUVEAU ---

            # --- Logique par Mode ---
            # S'exécute seulement si ce n'était pas une commande interne
            executed_command = None
            stdout, stderr = None, None

            if current_mode == "naturel":
                generated_command = get_command_from_natural_language(
                    user_input, model_to_use,
                    conversation_history=conversation_history
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
                        executed_command = generated_command
                        stdout, stderr = execute_command(executed_command)
                        print_result(stdout, stderr)
                else:
                    print(f"{cfg.COLOR_RED}Impossible de générer une commande pour cette demande.{cfg.COLOR_RESET}")

            elif current_mode == "commande":
                command_to_run = user_input
                if command_to_run.startswith("cd ") or command_to_run == "cd":
                    parts = command_to_run.split(maxsplit=1)
                    target_dir = parts[1] if len(parts) > 1 else "~"
                    change_directory(target_dir)
                    continue
                executed_command = command_to_run
                stdout, stderr = execute_command(executed_command)
                print_result(stdout, stderr)

            # --- Mise à jour historique contexte ET Analyse ---
            if executed_command is not None:
                conversation_history.append((executed_command, stdout, stderr))
                is_successful = stderr is None or not stderr.strip()
                use_ollama = True
                direct_analysis_output = None

                if is_successful:
                    if executed_command in cfg.SIMPLE_COMMANDS:
                         if executed_command == "pwd": direct_analysis_output = f"{cfg.COLOR_BLUE}Vous êtes actuellement dans le dossier : {stdout.strip()}{cfg.COLOR_RESET}"
                         elif executed_command == "whoami": direct_analysis_output = f"{cfg.COLOR_BLUE}Vous êtes connecté en tant que : {stdout.strip()}{cfg.COLOR_RESET}"
                         use_ollama = False
                    elif cfg.ECHO_XXD_PIPE in executed_command:
                         direct_analysis_output = f"{cfg.COLOR_BLUE}Le résultat décodé (echo | xxd -r -p) est :\n{stdout.strip()}{cfg.COLOR_RESET}"
                         use_ollama = False

                if use_ollama:
                    prompt_type = "detailed"
                    base_command = executed_command.split('|')[0].strip().split(' ')[0]
                    if base_command in cfg.SECURITY_TOOLS:
                        prompt_type = "security_analysis"
                    elif (executed_command == cfg.LS_COMMAND or executed_command.startswith(cfg.LS_COMMAND + " ")) and is_successful:
                        prompt_type = "simple_ls"

                    analysis_result = get_ollama_analysis(
                        executed_command, stdout, stderr, model_to_use, prompt_type=prompt_type,
                        conversation_history=conversation_history
                    )
                    print_analysis(analysis_result)
                else:
                    print_analysis(direct_analysis_output)

        except KeyboardInterrupt:
            print(f"\n{cfg.COLOR_YELLOW}Interruption reçue. Sauvegarde de l'historique et sortie...{cfg.COLOR_RESET}")
            break
        except Exception as e:
            print(f"\n{cfg.COLOR_RED}{cfg.COLOR_BOLD}Une erreur critique est survenue dans la boucle principale:{cfg.COLOR_RESET}")
            print(f"{cfg.COLOR_RED}{type(e).__name__}: {e}{cfg.COLOR_RESET}")
            print(f"{cfg.COLOR_YELLOW}Tentative de continuation...{cfg.COLOR_RESET}")

    print(f"\n{cfg.COLOR_BOLD}{cfg.COLOR_BLUE}Luciole terminé. Au revoir !{cfg.COLOR_RESET}")

if __name__ == "__main__":
    main()