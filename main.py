# main.py

import os
import sys
from collections import deque
from rich.console import Console
from rich.rule import Rule
import config as cfg
from history_manager import setup_history, add_history_entry
from shell_utils import execute_command, change_directory
# Importe la nouvelle fonction avec les autres
from ollama_client import get_ollama_analysis, get_command_from_natural_language, get_tool_suggestions

console = Console()

# --- MODIFICATION : print_analysis affiche maintenant le texte reçu ---
def print_analysis(analysis_result):
    console.rule("[bold cyan]🧠 Analyse Luciole")
    if analysis_result: # analysis_result contient le texte complet ou un message d'erreur
        # Applique la couleur bleue si ce n'est pas une erreur déjà formatée
        if not str(analysis_result).strip().startswith("[bold red]"):
             console.print(f"[blue]{analysis_result}[/blue]")
        else:
             console.print(analysis_result) # Affiche l'erreur formatée Rich
    else:
        # Cas où Ollama n'a vraiment rien retourné
        console.print("[italic](Aucune analyse générée par l'IA.)[/italic]")
# --- FIN MODIFICATION ---

# ... (print_result, is_dangerous, print_help_message, print_tool_suggestions inchangés) ...
def print_result(stdout, stderr):
    console.rule("[bold cyan]📊 Résultat Brut")
    has_output = False
    if stdout is not None and stdout.strip(): console.print(f"[green]Sortie standard:[/green]\n{stdout.strip()}"); has_output = True
    if stderr is not None and stderr.strip(): console.print(f"[red]Sortie d'erreur:[/red]\n{stderr.strip()}"); has_output = True
    if not has_output: console.print("(Aucune sortie notable)")

def is_dangerous(command):
    return any(keyword in command for keyword in cfg.DANGEROUS_KEYWORDS)

def print_help_message():
    console.rule("[bold cyan]❓ Aide Luciole")
    console.print("🦊 Luciole est un assistant de terminal utilisant Ollama.")
    console.print("Il analyse les commandes, traduit le langage naturel et suggère des outils.")
    console.print("Utilisez [yellow]/suggest_tools [description][/yellow] pour les suggestions.")
    console.print("\n[bold]Modes d'Opération :[/bold]")
    console.print(f"  💻 [green]commande[/green] : Exécute et analyse les commandes shell.")
    console.print(f"  🗣️ [magenta]naturel [/magenta] : Traduit le langage naturel en commande.")
    console.print("\n[bold]Commandes Spéciales :[/bold]")
    console.print(f"  [yellow]/mode[/yellow]           : Bascule entre les modes.")
    console.print(f"  [yellow]/help[/yellow]           : Affiche cette aide.")
    console.print(f"  [yellow]/suggest_tools ...[/yellow]: Suggère des outils.")
    console.print(f"  [yellow]quitter[/yellow]        : Quitte l'application.")
    console.print("\n[bold]Navigation :[/bold]")
    console.print(f"  Flèches [bold]Haut⬆️[/bold]/[bold]Bas⬇️[/bold] : Historique des commandes.")

def print_tool_suggestions(suggestions):
    console.rule("[bold cyan]🛠️ Suggestions d'Outils")
    if suggestions:
        if not str(suggestions).strip().startswith(cfg.COLOR_RED) and not str(suggestions).strip().startswith("[bold red]"):
             console.print(f"[blue]{suggestions}[/blue]")
        else:
             console.print(suggestions)
    else:
        console.print("(Aucune suggestion générée ou erreur lors de la requête.)")


def main():
    # ... (Initialisation inchangée) ...
    console.print(f"[bold blue]Bienvenue dans 🦊 Luciole v5 ![/bold blue]")
    console.print(f"[yellow]Assurez-vous qu'Ollama est lancé (ex: 'ollama run {cfg.DEFAULT_MODEL}').[/yellow]")
    setup_history(console=console) # <-- Appel modifié à setup_history (étape précédente)
    model_input = input(f"{cfg.COLOR_GREEN}Quel modèle Ollama utiliser ? [Défaut: {cfg.DEFAULT_MODEL}] > {cfg.COLOR_RESET}").strip()
    model_to_use = model_input if model_input else cfg.DEFAULT_MODEL
    console.print(f"[yellow]Utilisation du modèle : {model_to_use}[/yellow]")
    current_mode = "commande"
    console.print(f"\n[green]Mode actuel : {current_mode}. Tapez '/mode' pour changer.[/green]")
    console.print(f"[green]Commandes spéciales: /help, /suggest_tools [tâche], quitter[/green]")
    conversation_history = deque(maxlen=3)

    while True:
        try:
            # ... (Prompt et commandes internes inchangés) ...
            current_dir_short = os.path.basename(os.getcwd())
            mode_icon = "💻" if current_mode == "commande" else "🗣️"
            prompt_color = cfg.COLOR_GREEN if current_mode == "commande" else cfg.COLOR_MAGENTA
            prompt_indicator = "Commande >" if current_mode == "commande" else "Parlez >"
            prompt_text = (f"\n{cfg.COLOR_CYAN}({current_dir_short}) {mode_icon} {cfg.COLOR_RESET}"
                           f"{cfg.COLOR_BOLD}{prompt_color}"
                           f"{prompt_indicator} {cfg.COLOR_RESET}")
            user_input = input(prompt_text).strip()

            if user_input.lower() == 'quitter': break
            if not user_input: continue
            add_history_entry(user_input)

            if user_input.lower() == "/help": print_help_message(); continue
            if user_input == "/mode":
                current_mode = "naturel" if current_mode == "commande" else "commande"
                console.print(f"[yellow]Passage en mode : {current_mode}[/yellow]"); continue
            elif user_input.lower().startswith("/suggest_tools "):
                task_description = user_input[len("/suggest_tools "):].strip()
                if not task_description: console.print(f"[yellow]Veuillez décrire la tâche...[/yellow]"); continue
                suggestions = None
                with console.status("[bold yellow]🤔 Recherche d'outils...", spinner="dots"):
                    suggestions = get_tool_suggestions(task_description, model_to_use)
                print_tool_suggestions(suggestions); continue


            executed_command = None
            stdout, stderr = None, None

            if current_mode == "naturel":
                # ... (Logique naturelle inchangée jusqu'à l'appel) ...
                generated_command = None
                with console.status("[bold yellow]🤔 Traduction en cours...", spinner="dots"):
                     generated_command = get_command_from_natural_language(
                        user_input, model_to_use, conversation_history=conversation_history
                     )
                if generated_command:
                    console.print(f"[yellow]Commande suggérée : {generated_command}[/yellow]")
                    execute_it = True
                    if is_dangerous(generated_command):
                         confirm = input(f"{cfg.COLOR_BOLD}{cfg.COLOR_RED}⚠️ ATTENTION : Commande dangereuse ! Exécuter '{generated_command}' ? (o/N) > {cfg.COLOR_RESET}").lower()
                         if confirm != 'o': console.print(f"[yellow]Exécution annulée.[/yellow]"); execute_it = False
                    if execute_it:
                        executed_command = generated_command
                        stdout, stderr = execute_command(executed_command)
                        print_result(stdout, stderr)
                else: console.print(f"[red]Impossible de générer une commande...[/red]")

            elif current_mode == "commande":
                # ... (Logique commande inchangée jusqu'à l'appel) ...
                command_to_run = user_input
                if command_to_run.startswith("cd ") or command_to_run == "cd":
                    parts = command_to_run.split(maxsplit=1); target_dir = parts[1] if len(parts) > 1 else "~"
                    change_directory(target_dir); continue
                executed_command = command_to_run
                stdout, stderr = execute_command(executed_command)
                print_result(stdout, stderr)


            if executed_command is not None:
                conversation_history.append((executed_command, stdout, stderr))
                is_successful = stderr is None or not stderr.strip()
                use_ollama = True
                direct_analysis_output = None

                if is_successful: # Analyses directes
                    if executed_command in cfg.SIMPLE_COMMANDS:
                        if executed_command == "pwd": direct_analysis_output = f"[blue]Vous êtes dans : {stdout.strip()}[/blue]"
                        elif executed_command == "whoami": direct_analysis_output = f"[blue]Vous êtes : {stdout.strip()}[/blue]"
                        use_ollama = False
                    elif cfg.ECHO_XXD_PIPE in executed_command:
                        direct_analysis_output = f"[blue]Résultat décodé :\n{stdout.strip()}[/blue]"
                        use_ollama = False

                if use_ollama: # Analyse Ollama
                    prompt_type = "detailed"
                    base_command = executed_command.split('|')[0].strip().split(' ')[0]
                    if base_command in cfg.SECURITY_TOOLS: prompt_type = "security_analysis"
                    elif (executed_command == cfg.LS_COMMAND or executed_command.startswith(cfg.LS_COMMAND + " ")) and is_successful: prompt_type = "simple_ls"

                    analysis_result = None
                    status_msg = f"[bold yellow]🤔 Analyse {'spécialisée ' if prompt_type == 'security_analysis' else ''}en cours..."
                    with console.status(status_msg, spinner="dots"):
                        # --- MODIFICATION : Appel SANS l'argument console ---
                        analysis_result = get_ollama_analysis(
                            executed_command, stdout, stderr, model_to_use, prompt_type=prompt_type,
                            conversation_history=conversation_history
                            # Pas de console=console ici
                        )
                        # --- FIN MODIFICATION ---
                    # print_analysis se charge d'afficher analysis_result
                    print_analysis(analysis_result)
                else:
                    # Afficher l'analyse directe formatée Rich
                    print_analysis(direct_analysis_output)

        # ... (Gestion exceptions inchangée) ...
        except KeyboardInterrupt: console.print(f"\n[yellow]Interruption reçue...[/yellow]"); break
        except Exception as e:
            console.print(f"\n[bold red]Erreur critique boucle principale:[/bold red]")
            console.print_exception(show_locals=False); console.print(f"[yellow]Tentative de continuation...[/yellow]")

    console.print(f"\n[bold blue]🦊 Luciole terminé. Au revoir ![/bold blue]")

if __name__ == "__main__":
    main()