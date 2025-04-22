# ollama_client.py

import requests
import json
import re
import sys
from collections import deque
# Plus besoin d'importer Console ici si on ne l'utilise que pour type hinting avant
# from rich.console import Console
from config import (
    OLLAMA_API_URL, SYSTEM_PROMPT, OLLAMA_TIMEOUT_ANALYSIS, OLLAMA_TIMEOUT_TRANSLATE,
    COLOR_YELLOW, COLOR_RED, COLOR_RESET, LS_COMMAND, COLOR_BLUE, COLOR_BOLD
)

# ... (fonction format_history_for_prompt inchangée) ...
def format_history_for_prompt(history: deque, max_len_per_output: int = 200) -> str:
    if not history: return ""
    formatted_string = "History of previous interactions (oldest first, most recent last):\n---\n"
    for i, (cmd, out, err) in enumerate(history):
        if i > 0: formatted_string += "---\n"
        formatted_string += f"Interaction {i+1}:\nCommand: `{cmd}`\n"
        out_str = out.strip() if out else "(no stdout)"
        err_str = err.strip() if err else "(no stderr)"
        if len(out_str) > max_len_per_output: out_str = out_str[:max_len_per_output // 2] + "\n...\n" + out_str[-max_len_per_output // 2:]
        if len(err_str) > max_len_per_output: err_str = err_str[:max_len_per_output // 2] + "\n...\n" + err_str[-max_len_per_output // 2:]
        formatted_string += f"Stdout:\n```\n{out_str}\n```\n"
        if err_str != "(no stderr)": formatted_string += f"Stderr:\n```\n{err_str}\n```\n"
    formatted_string += "---\nCurrent Request:\n"
    return formatted_string

# --- MODIFICATION : get_ollama_analysis ne fait plus l'affichage streamé ---
def get_ollama_analysis(command, stdout, stderr, model_name,
                        prompt_type="detailed", conversation_history: deque = None):
                        # Pas de paramètre console ici
    """ Interroge l'API Ollama, accumule la réponse streamée et la retourne."""

    stdout_str = stdout if stdout is not None else "(Erreur lors de la récupération de stdout)"
    stderr_str = stderr if stderr is not None else "(Erreur lors de la récupération de stderr)"
    history_context = format_history_for_prompt(conversation_history)
    task_prompt = ""
    base_command = command.split('|')[0].strip().split(' ')[0]

    # ... (logique if/elif/else pour définir task_prompt reste inchangée) ...
    if prompt_type == "simple_ls":
        task_prompt = f"""La commande `{LS_COMMAND}` (ou une variante) vient d'être exécutée et a retourné :\n```\n{stdout_str.strip()}\n```\nEn tenant compte de l'historique ci-dessus si pertinent, décris cette sortie en une seule phrase très simple et naturelle en français. Commence par "Dans ce dossier, il y a" ou similaire."""
    elif prompt_type == "security_analysis":
        task_prompt = f"""La commande de l'outil de sécurité `{base_command}` suivante vient d'être exécutée :\n`{command}`\n\nSon résultat standard (stdout) est :\n```\n{stdout_str.strip() if stdout_str else "(aucun)"}\n```\n\nSon résultat d'erreur (stderr) est :\n```\n{stderr_str.strip() if stderr_str else "(aucun)"}\n```\n\n**Instructions STRICTES pour Luciole (Expert Cybersécurité) :**\nEn te basant EXCLUSIVEMENT sur l'historique de conversation et les sorties (stdout/stderr) fournies ci-dessus pour la commande `{command}` :\n1.  **Résume les FAITS CLÉS de sécurité trouvés DANS LA SORTIE.** Mentionne UNIQUEMENT ce qui est visible (ports ouverts, services/versions identifiés, chemins découverts, vulnérabilités *explicitement rapportées par l'outil*). Ne fais PAS d'hypothèses ou de déductions non présentes dans le texte. Sois concis et factuel.\n2.  **Identifie les options/flags principaux** réellement utilisés dans la commande `{command}` (par exemple, `-sV`, `-p`, `-h`, `-w`). Explique très brièvement leur but si tu es certain, sinon liste-les simplement. N'invente PAS d'options non présentes dans la commande.\n3.  **Basé STRICTEMENT sur les FAITS résumés à l'étape 1**, suggère 1 ou 2 étapes suivantes LOGIQUES et PERTINENTES pour un pentest/audit. Formule-les si possible de manière conditionnelle (Ex: "SI le port 443 est ouvert, ALORS suggérer `nikto -h <target>`.", "SI un chemin `/api` est trouvé, ALORS suggérer de l'explorer."). Ne suggère PAS d'actions basées on des services/infos non trouvés dans la sortie.\n4.  Si la sortie stdout mentionne des **versions logicielles précises**, recherche des **CVEs** potentiels pour *ces versions spécifiques*. Indique le CVE si trouvé, mais précise clairement que c'est une piste et nécessite une vérification manuelle. Ne liste pas de CVEs pour des versions non mentionnées.\n5.  Si stderr n'est pas vide, explique l'erreur rapportée dans stderr et suggère une correction si évidente.\nSois factuel, technique, et évite toute information non directement supportée par la sortie de la commande ou l'historique."""
    else: # prompt_type == "detailed"
        task_prompt = f"""La commande suivante vient d'être exécutée :\n`{command}`\n\nSon résultat standard (stdout) est :\n```\n{stdout_str.strip() if stdout_str else "(aucun)"}\n```\n\nSon résultat d'erreur (stderr) est :\n```\n{stderr_str.strip() if stderr_str else "(aucun)"}\n```\n\nEn te basant sur ton rôle d'expert Luciole ET sur l'historique de conversation fourni ci-dessus, analyse ce résultat. Explique ce qui s'est passé (succès, erreur...). Si pertinent (erreur, outil réseau/sécu comme nmap), suggère des commandes de suivi ou des considérations de sécurité en lien avec le contexte. Sois bref pour les succès simples."""

    prompt = history_context + task_prompt
    payload = { "model": model_name, "system": SYSTEM_PROMPT, "prompt": prompt, "stream": True }
    analysis_content = ""
    error_occurred = False

    try:
        # Le message d'attente est géré par main.py
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=OLLAMA_TIMEOUT_ANALYSIS, stream=True)
        response.raise_for_status()

        # --- Boucle de Streaming SANS AFFICHAGE DIRECT ---
        for line in response.iter_lines():
            if line:
                try:
                    decoded_line = line.decode('utf-8')
                    data = json.loads(decoded_line)
                    chunk = data.get("response", "")
                    analysis_content += chunk # On accumule seulement
                    if data.get("done"):
                         break
                # Gestion erreurs mineures pendant le stream
                except json.JSONDecodeError: pass # Ignore decode errors silently for now
                except Exception: error_occurred = True; break # Break on other stream errors

        # --- MODIFICATION : Retourne le contenu accumulé ou une chaîne vide ---
        return analysis_content if not error_occurred else "" # Retourne le texte ou "" si erreur stream

    # --- Gestion des erreurs globales ---
    except requests.exceptions.ConnectionError:
        # Retourne le message d'erreur formaté pour Rich
        return (f"[bold red]Erreur : Connexion Ollama impossible.[/bold red]\n"
                   f"[red]Vérifiez lancement ('ollama run {model_name}') et URL {OLLAMA_API_URL}[/red]")
    except requests.exceptions.Timeout:
        return f"[bold red]Erreur : Timeout ({OLLAMA_TIMEOUT_ANALYSIS}s) connexion Ollama.[/bold red]"
    except requests.exceptions.RequestException as e:
        return f"[bold red]Erreur requête Ollama (Analyse) : {e}[/bold red]"
    except Exception as e:
        return f"[bold red]Erreur inattendue (Analyse Ollama) : {type(e).__name__}: {e}[/bold red]"

# ... (get_command_from_natural_language et get_tool_suggestions restent inchangés) ...
def get_command_from_natural_language(natural_language_input, model_name,
                                      conversation_history: deque = None):
    history_context = format_history_for_prompt(conversation_history)
    task_prompt = f"""Traduis la requête utilisateur suivante en UNE SEULE commande shell Linux standard et exécutable. Réponds UNIQUEMENT avec la commande exacte, sans explication, formatage, salutation, ou texte supplémentaire. Si la requête est ambiguë, dangereuse, nécessite plusieurs étapes, ou si tu ne peux pas la traduire en une commande shell unique et raisonnable, réponds exactement avec le mot 'CMD_ERROR'.
IMPORTANT: Utilise l'historique de conversation fourni ci-dessus pour comprendre les références implicites ('le fichier précédent', 'cette erreur', etc.).

Requête utilisateur : "{natural_language_input}"

Commande shell :"""
    prompt = history_context + task_prompt
    payload = { "model": model_name, "system": SYSTEM_PROMPT, "prompt": prompt, "stream": False }
    try:
        print(f"\n{COLOR_YELLOW}Traduction en cours (avec contexte)...{COLOR_RESET}", flush=True)
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=OLLAMA_TIMEOUT_TRANSLATE)
        response.raise_for_status()
        data = response.json()
        generated_output = data.get("response", "").strip()
        print(f"{COLOR_YELLOW}Traduction reçue (brute) : '{generated_output}'{COLOR_RESET}")
        match = re.search(r'```(?:bash\n)?(.*?)\n?```', generated_output, re.DOTALL | re.IGNORECASE)
        if match: cleaned_command = match.group(1).strip()
        else:
            cleaned_command = generated_output.replace('`', '').strip()
            if cleaned_command.lower().startswith("commande shell :"): cleaned_command = cleaned_command.split(":", 1)[1].strip()
        if not cleaned_command or "CMD_ERROR" in cleaned_command or '\n' in cleaned_command:
            print(f"{COLOR_RED}Ollama n'a pas retourné une commande unique valide (Nettoyée: '{cleaned_command}').{COLOR_RESET}"); return None
        print(f"{COLOR_YELLOW}Commande nettoyée : '{cleaned_command}'{COLOR_RESET}"); return cleaned_command
    except requests.exceptions.ConnectionError: print(f"\n{COLOR_RED}{COLOR_BOLD}Erreur connexion Ollama (Traduction).{COLOR_RESET}"); return None
    except requests.exceptions.Timeout: print(f"\n{COLOR_RED}{COLOR_BOLD}Timeout ({OLLAMA_TIMEOUT_TRANSLATE}s) Ollama (Traduction).{COLOR_RESET}"); return None
    except requests.exceptions.RequestException as e: print(f"\n{COLOR_RED}{COLOR_BOLD}Erreur requête Ollama (Traduction): {e}{COLOR_RESET}"); return None
    except Exception as e: print(f"\n{COLOR_RED}{COLOR_BOLD}Erreur inattendue (Traduction Ollama): {type(e).__name__}: {e}{COLOR_RESET}"); return None

def get_tool_suggestions(task_description: str, model_name: str):
    prompt = f"""Agissant en tant que Luciole, expert en ligne de commande Linux et cybersécurité :
L'utilisateur souhaite accomplir la tâche suivante : "{task_description}"
En te basant sur cette description de tâche, suggère 3 à 5 outils en ligne de commande pertinents, couramment utilisés sous Linux en cybersécurité (pentest, OSINT, analyse, etc.), qui pourraient aider à réaliser cette tâche.
Pour chaque outil suggéré :
1.  Donne le **nom de la commande** (ex: `nmap`, `gobuster`, `nikto`).
2.  Fournis une **brève description (1 phrase)** expliquant son utilité principale pour la tâche décrite par l'utilisateur.
Formate la sortie clairement, par exemple sous forme de liste numérotée. Concentre-toi uniquement sur les outils CLI pertinents. Sois concis et précis."""
    payload = { "model": model_name, "system": SYSTEM_PROMPT, "prompt": prompt, "stream": False }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=OLLAMA_TIMEOUT_TRANSLATE)
        response.raise_for_status()
        data = response.json()
        suggestions_text = data.get("response", "").strip()
        if not suggestions_text: return "(L'IA n'a retourné aucune suggestion.)"
        return suggestions_text
    except requests.exceptions.ConnectionError: return (f"{COLOR_RED}{COLOR_BOLD}Erreur : Connexion Ollama impossible.{COLOR_RESET}\n{COLOR_RED}Vérifiez lancement et URL {OLLAMA_API_URL}{COLOR_RESET}")
    except requests.exceptions.Timeout: return f"{COLOR_RED}{COLOR_BOLD}Erreur : Timeout ({OLLAMA_TIMEOUT_TRANSLATE}s) Ollama (Suggestion).{COLOR_RESET}"
    except requests.exceptions.RequestException as e: return f"{COLOR_RED}{COLOR_BOLD}Erreur requête Ollama (Suggestion): {e}{COLOR_RESET}"
    except Exception as e: return f"{COLOR_RED}{COLOR_BOLD}Erreur inattendue (Suggestion Ollama): {type(e).__name__}: {e}{COLOR_RESET}"