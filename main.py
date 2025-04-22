#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main.py : Point d'entrée principal pour Foxi v5 (structuré)

import os
import sys

# Importer les modules du projet
import config as cfg
from history_manager import setup_history, add_history_entry
from shell_utils import execute_command, change_directory
from ollama_client import get_ollama_analysis, get_command_from_natural_language

def print_result(stdout, stderr):
    # ... (fonction inchangée) ...
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


# --- MODIFICATION : print_analysis pour gérer le retour de la fonction streamée ---
def print_analysis(analysis_result):
    """
    Affiche l'en-tête et le pied de page de l'analyse.
    Si analysis_result contient du texte (cas d'erreur retourné par ollama_client), l'affiche.
    Sinon (analysis_result est None ou ""), suppose que l'analyse a été affichée en streaming.
    """
    print(f"\n{cfg.COLOR_CYAN}--- Analyse Foxi ---{cfg.COLOR_RESET}")
    if analysis_result: # Si ollama_client a retourné un message (probablement une erreur)
        # Les erreurs devraient déjà être formatées/colorées par ollama_client
        print(analysis_result)
    # else:
        # Si analysis_result est None ou "", l'affichage a été fait par le stream
        # print("(Analyse affichée en temps réel)") # Message optionnel
    print(f"{cfg.COLOR_CYAN}--------------------{cfg.COLOR_RESET}")

def is_dangerous(command):
    # ... (fonction inchangée) ...
    return any(keyword in command for keyword in cfg.DANGEROUS_KEYWORDS)

def main():
    # ... (début de la fonction main inchangé) ...
    print(f"{cfg.COLOR_BOLD}{cfg.COLOR_BLUE}Bienvenue dans l'outil de commande assisté Foxi v5 !{cfg.COLOR_RESET}")
    print(f"{cfg.COLOR_YELLOW}Assurez-vous qu'Ollama est lancé (ex: 'ollama run {cfg.DEFAULT_MODEL}').{cfg.COLOR_RESET}")
    setup_history()
    model_input = input(f"{cfg.COLOR_GREEN}Quel modèle Ollama utiliser ? [Défaut: {cfg.DEFAULT_MODEL}] > {cfg.COLOR_RESET}").strip()
    model_to_use = model_input if model_input else cfg.DEFAULT_MODEL
    print(f"{cfg.COLOR_YELLOW}Utilisation du modèle : {model_to_use}{cfg.COLOR_RESET}")
    current_mode = "commande"
    print(f"\n{cfg.COLOR_GREEN}Mode actuel : {current_mode}. Tapez '/mode' pour changer.{cfg.COLOR_RESET}")
    print(f"{cfg.COLOR_GREEN}Utilisez les flèches Haut/Bas pour l'historique. Tapez 'quitter' pour arrêter.{cfg.COLOR_RESET}")

    while True:
        try:
            # ... (gestion du prompt et des commandes internes inchangée) ...
            current_dir_short = os.path.basename(os.getcwd())
            prompt_color = cfg.COLOR_GREEN if current_mode == "commande" else cfg.COLOR_MAGENTA
            prompt_indicator = "Commande >" if current_mode == "commande" else "Parlez >"
            prompt_text = (f"\n{cfg.COLOR_CYAN}({current_dir_short}) "
                           f"{cfg.COLOR_RESET}{cfg.COLOR_BOLD}{prompt_color}"
                           f"{prompt_indicator} {cfg.COLOR_RESET}")
            user_input = input(prompt_text).strip()

            if user_input.lower() == 'quitter': break
            if not user_input: continue
            if user_input == "/mode":
                current_mode = "naturel" if current_mode == "commande" else "commande"
                print(f"{cfg.COLOR_YELLOW}Passage en mode : {current_mode}{cfg.COLOR_RESET}")
                add_history_entry(user_input)
                continue
            add_history_entry(user_input)


            if current_mode == "naturel":
                # --- MODE NATUREL ---
                generated_command = get_command_from_natural_language(user_input, model_to_use)

                if generated_command:
                    print(f"{cfg.COLOR_YELLOW}Commande suggérée : {generated_command}{cfg.COLOR_RESET}")
                    execute_it = True
                    if is_dangerous(generated_command):
                        confirm = input(f"{cfg.COLOR_BOLD}{cfg.COLOR_RED}ATTENTION : Commande potentiellement dangereuse ! "
                                        f"Exécuter '{generated_command}' ? (o/N) > {cfg.COLOR_RESET}").lower()
                        if confirm != 'o':
                            print(f"{cfg.COLOR_YELLOW}Exécution annulée.{cfg.COLOR_RESET}")
                            execute_it = False

                    if execute_it:
                        stdout, stderr = execute_command(generated_command)
                        print_result(stdout, stderr)
                        # --- MODIFICATION : Appel pour l'analyse après commande naturelle ---
                        # L'analyse de la commande générée utilisera aussi le streaming
                        analysis_result = get_ollama_analysis(generated_command, stdout, stderr, model_to_use, prompt_type="detailed")
                        print_analysis(analysis_result) # Affiche en-tête/pied et erreurs éventuelles
                else:
                    print(f"{cfg.COLOR_RED}Impossible de générer une commande pour cette demande.{cfg.COLOR_RESET}")


            elif current_mode == "commande":
                # --- MODE COMMANDE ---
                command_to_run = user_input
                analysis_result = None # Sera soit None/"" (succès stream), soit un message d'erreur

                if command_to_run.startswith("cd ") or command_to_run == "cd":
                    parts = command_to_run.split(maxsplit=1)
                    target_dir = parts[1] if len(parts) > 1 else "~"
                    change_directory(target_dir)
                    continue

                stdout, stderr = execute_command(command_to_run)
                print_result(stdout, stderr)

                is_successful = stderr is None or not stderr.strip()
                base_command = command_to_run.split('|')[0].strip().split(' ')[0]

                # --- GESTION SIMPLIFIÉE : On appelle toujours Ollama pour l'analyse (ou les messages directs) ---
                # --- MAIS on garde la logique pour les messages directs qui ne nécessitent PAS Ollama ---
                use_ollama = True
                direct_analysis_output = None # Pour stocker les messages directs non-Ollama

                if is_successful:
                    if command_to_run in cfg.SIMPLE_COMMANDS:
                         if command_to_run == "pwd":
                             direct_analysis_output = f"{cfg.COLOR_BLUE}Vous êtes actuellement dans le dossier : {stdout.strip()}{cfg.COLOR_RESET}"
                         elif command_to_run == "whoami":
                             direct_analysis_output = f"{cfg.COLOR_BLUE}Vous êtes connecté en tant que : {stdout.strip()}{cfg.COLOR_RESET}"
                         use_ollama = False # Pas besoin d'Ollama pour ces cas
                    elif cfg.ECHO_XXD_PIPE in command_to_run:
                         direct_analysis_output = f"{cfg.COLOR_BLUE}Le résultat décodé (echo | xxd -r -p) est :\n{stdout.strip()}{cfg.COLOR_RESET}"
                         use_ollama = False # Pas besoin d'Ollama ici non plus

                if use_ollama:
                    # Déterminer le type de prompt pour Ollama
                    prompt_type = "detailed"
                    if command_to_run == cfg.LS_COMMAND or command_to_run.startswith(cfg.LS_COMMAND + " "):
                        if is_successful: # Utiliser le prompt simple seulement si ls a réussi
                             prompt_type = "simple_ls"

                    # --- MODIFICATION : Appel à la fonction d'analyse streamée ---
                    analysis_result = get_ollama_analysis(command_to_run, stdout, stderr, model_to_use, prompt_type=prompt_type)
                    print_analysis(analysis_result) # Affiche en-tête/pied et erreurs éventuelles
                else:
                    # Afficher le message direct généré sans Ollama
                    print_analysis(direct_analysis_output)


        except KeyboardInterrupt:
            print(f"\n{cfg.COLOR_YELLOW}Interruption reçue. Sauvegarde de l'historique et sortie...{cfg.COLOR_RESET}")
            break
        except Exception as e:
            print(f"\n{cfg.COLOR_RED}{cfg.COLOR_BOLD}Une erreur critique est survenue dans la boucle principale:{cfg.COLOR_RESET}")
            print(f"{cfg.COLOR_RED}{type(e).__name__}: {e}{cfg.COLOR_RESET}")
            print(f"{cfg.COLOR_YELLOW}Tentative de continuation...{cfg.COLOR_RESET}")

    print(f"\n{cfg.COLOR_BOLD}{cfg.COLOR_BLUE}Foxi terminé. Au revoir !{cfg.COLOR_RESET}")

if __name__ == "__main__":
    main()