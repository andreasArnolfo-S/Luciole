# -*- coding: utf-8 -*-
# ollama_client.py : Fonctions pour interagir avec l'API Ollama

import requests
import json
import re
import sys
from collections import deque # Pour l'historique de contexte
from config import (
    OLLAMA_API_URL, SYSTEM_PROMPT, OLLAMA_TIMEOUT_ANALYSIS, OLLAMA_TIMEOUT_TRANSLATE,
    COLOR_YELLOW, COLOR_RED, COLOR_RESET, LS_COMMAND, COLOR_BLUE, COLOR_BOLD,
    # Assure-toi que SECURITY_TOOLS est importable si tu en as besoin ici,
    # mais normalement c'est main.py qui l'utilise pour choisir le prompt_type.
)

# --- Fonction pour formater l'historique ---
def format_history_for_prompt(history: deque, max_len_per_output: int = 200) -> str:
    """Formate l'historique de conversation pour l'inclure dans un prompt Ollama."""
    if not history:
        return ""

    # Commence par le plus ancien, finit par le plus récent
    formatted_string = "History of previous interactions (oldest first, most recent last):\n"
    formatted_string += "---\n"
    for i, (cmd, out, err) in enumerate(history):
        if i > 0:
             formatted_string += "---\n" # Séparateur entre interactions

        formatted_string += f"Interaction {i+1}:\n"
        formatted_string += f"Command: `{cmd}`\n"

        # Tronquer stdout et stderr pour éviter des prompts trop longs
        out_str = out.strip() if out else "(no stdout)"
        err_str = err.strip() if err else "(no stderr)"

        if len(out_str) > max_len_per_output:
            out_str = out_str[:max_len_per_output // 2] + "\n...\n" + out_str[-max_len_per_output // 2:]
        if len(err_str) > max_len_per_output:
             err_str = err_str[:max_len_per_output // 2] + "\n...\n" + err_str[-max_len_per_output // 2:]

        formatted_string += f"Stdout:\n```\n{out_str}\n```\n"
        if err_str != "(no stderr)":
             formatted_string += f"Stderr:\n```\n{err_str}\n```\n"

    formatted_string += "---\n"
    formatted_string += "Current Request:\n" # Indique où commence la nouvelle requête

    return formatted_string
# --- FIN Fonction formatage historique ---


# --- Fonction d'analyse Ollama (modifiée pour contexte et prompt sécurité) ---
def get_ollama_analysis(command, stdout, stderr, model_name,
                        prompt_type="detailed", conversation_history: deque = None): # <-- Signature modifiée
    """ Interroge l'API Ollama locale pour analyser la sortie (avec STREAMING et CONTEXTE). """
    stdout_str = stdout if stdout is not None else "(Erreur lors de la récupération de stdout)"
    stderr_str = stderr if stderr is not None else "(Erreur lors de la récupération de stderr)"

    # Formater l'historique pour le prompt (sera vide si conversation_history est None)
    history_context = format_history_for_prompt(conversation_history)

    # Définir le prompt spécifique à la tâche actuelle basé sur prompt_type
    task_prompt = ""
    base_command = command.split('|')[0].strip().split(' ')[0] # Utile pour le prompt sécurité

    if prompt_type == "simple_ls":
         task_prompt = f"""La commande `{LS_COMMAND}` (ou une variante) vient d'être exécutée et a retourné :

{stdout_str.strip()}

En tenant compte de l'historique ci-dessus si pertinent, décris cette sortie en une seule phrase très simple et naturelle en français. Commence par "Dans ce dossier, il y a" ou similaire."""

    elif prompt_type == "security_analysis": # <-- Nouveau type de prompt
        task_prompt = f"""La commande de l'outil de sécurité `{base_command}` suivante vient d'être exécutée :
`{command}`

Son résultat standard (stdout) est :

{stdout_str.strip() if stdout_str else "(aucun)"}


Son résultat d'erreur (stderr) est :

{stderr_str.strip() if stderr_str else "(aucun)"}


**Instructions STRICTES pour Foxi (Expert Cybersécurité) :**
En te basant EXCLUSIVEMENT sur l'historique de conversation et les sorties (stdout/stderr) fournies ci-dessus pour la commande `{command}` :

1.  **Résume les FAITS CLÉS de sécurité trouvés DANS LA SORTIE.** Mentionne UNIQUEMENT ce qui est visible (ports ouverts, services/versions identifiés, chemins découverts, vulnérabilités *explicitement rapportées par l'outil*). Ne fais PAS d'hypothèses ou de déductions non présentes dans le texte. Sois concis et factuel.
2.  **Identifie les options/flags principaux** réellement utilisés dans la commande `{command}` (par exemple, `-sV`, `-p`, `-h`, `-w`). Explique très brièvement leur but si tu es certain, sinon liste-les simplement. N'invente PAS d'options non présentes dans la commande.
3.  **Basé STRICTEMENT sur les FAITS résumés à l'étape 1**, suggère 1 ou 2 étapes suivantes LOGIQUES et PERTINENTES pour un pentest/audit. Formule-les si possible de manière conditionnelle (Ex: "SI le port 443 est ouvert, ALORS suggérer `nikto -h <target>`.", "SI un chemin `/api` est trouvé, ALORS suggérer de l'explorer."). Ne suggère PAS d'actions basées on des services/infos non trouvés dans la sortie.
4.  Si la sortie stdout mentionne des **versions logicielles précises**, recherche des **CVEs** potentiels pour *ces versions spécifiques*. Indique le CVE si trouvé, mais précise clairement que c'est une piste et nécessite une vérification manuelle. Ne liste pas de CVEs pour des versions non mentionnées.
5.  Si stderr n'est pas vide, explique l'erreur rapportée dans stderr et suggère une correction si évidente.

Sois factuel, technique, et évite toute information non directement supportée par la sortie de la commande ou l'historique."""

    else: # prompt_type == "detailed" (par défaut pour les autres commandes)
         task_prompt = f"""La commande suivante vient d'être exécutée :
`{command}`

Son résultat standard (stdout) est :

{stdout_str.strip() if stdout_str else "(aucun)"}


Son résultat d'erreur (stderr) est :

{stderr_str.strip() if stderr_str else "(aucun)"}


En te basant sur ton rôle d'expert Foxi ET sur l'historique de conversation fourni ci-dessus, analyse ce résultat. Explique ce qui s'est passé (succès, erreur...). Si pertinent (erreur, outil réseau/sécu comme nmap), suggère des commandes de suivi ou des considérations de sécurité en lien avec le contexte. Sois bref pour les succès simples."""

    # Assembler le prompt final
    prompt = history_context + task_prompt

    payload = { "model": model_name, "system": SYSTEM_PROMPT, "prompt": prompt, "stream": True }
    analysis_content = ""
    error_occurred = False

    try:
        wait_msg = f"\n{COLOR_YELLOW}Analyse {'spécialisée' if prompt_type == 'security_analysis' else 'en cours'} (avec contexte)...{COLOR_RESET}"
        print(wait_msg, flush=True)
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=OLLAMA_TIMEOUT_ANALYSIS, stream=True)
        response.raise_for_status()
        print(f"{COLOR_BLUE}", end='') # Appliquer couleur pour l'analyse
        for line in response.iter_lines():
            if line:
                try:
                    decoded_line = line.decode('utf-8')
                    data = json.loads(decoded_line)
                    chunk = data.get("response", "")
                    analysis_content += chunk
                    print(chunk, end='', flush=True)
                    if data.get("done"): break
                except json.JSONDecodeError: print(f"\n{COLOR_RED}Erreur décodage JSON stream.{COLOR_RESET}")
                except Exception as e: print(f"\n{COLOR_RED}Erreur stream: {e}{COLOR_RESET}"); error_occurred = True; break
        print(f"{COLOR_RESET}") # Rétablir couleur par défaut
        # Retourne None si le stream a fonctionné (l'affichage est fait), "" si rien reçu, ou msg d'erreur
        return None if analysis_content and not error_occurred else ""
    # --- Gestion des erreurs (simplifiée pour la lisibilité) ---
    except requests.exceptions.ConnectionError:
        err_msg = (f"\n{COLOR_RED}{COLOR_BOLD}Erreur : Connexion Ollama impossible.{COLOR_RESET}\n"
                   f"{COLOR_RED}Vérifiez lancement ('ollama run {model_name}') et URL {OLLAMA_API_URL}{COLOR_RESET}")
        print(err_msg); return err_msg
    except requests.exceptions.Timeout:
        err_msg = f"\n{COLOR_RED}{COLOR_BOLD}Erreur : Timeout ({OLLAMA_TIMEOUT_ANALYSIS}s) connexion Ollama.{COLOR_RESET}"
        print(err_msg); return err_msg
    except requests.exceptions.RequestException as e:
        err_msg = f"\n{COLOR_RED}{COLOR_BOLD}Erreur requête Ollama (Analyse) : {e}{COLOR_RESET}"
        print(err_msg); return err_msg
    except Exception as e:
        err_msg = f"\n{COLOR_RED}{COLOR_BOLD}Erreur inattendue (Analyse Ollama) : {type(e).__name__}: {e}{COLOR_RESET}"
        print(err_msg); return err_msg


# --- Fonction de traduction NL (modifiée pour contexte) ---
def get_command_from_natural_language(natural_language_input, model_name,
                                      conversation_history: deque = None): # <-- Signature modifiée
    """ Demande à Ollama de traduire une phrase en commande shell (avec CONTEXTE). """

    # Formater l'historique pour le prompt
    history_context = format_history_for_prompt(conversation_history)

    # Définir le prompt spécifique à la tâche actuelle
    task_prompt = f"""Traduis la requête utilisateur suivante en UNE SEULE commande shell Linux standard et exécutable. Réponds UNIQUEMENT avec la commande exacte, sans explication, formatage, salutation, ou texte supplémentaire. Si la requête est ambiguë, dangereuse, nécessite plusieurs étapes, ou si tu ne peux pas la traduire en une commande shell unique et raisonnable, réponds exactement avec 'CMD_ERROR'.
IMPORTANT: Utilise l'historique de conversation fourni ci-dessus pour comprendre les références implicites ('le fichier précédent', 'cette erreur', etc.).

Requête utilisateur : "{natural_language_input}"

Commande shell :"""

    # Assembler le prompt final
    prompt = history_context + task_prompt

    payload = { "model": model_name, "system": SYSTEM_PROMPT, "prompt": prompt, "stream": False }

    # --- Logique d'appel API non-streamée et gestion d'erreur ---
    try:
        print(f"\n{COLOR_YELLOW}Traduction en cours (avec contexte)...{COLOR_RESET}", flush=True)
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=OLLAMA_TIMEOUT_TRANSLATE)
        response.raise_for_status()
        data = response.json()
        generated_output = data.get("response", "").strip()
        print(f"{COLOR_YELLOW}Traduction reçue (brute) : '{generated_output}'{COLOR_RESET}")
        # Nettoyage de la réponse (retirer ```, etc.)
        match = re.search(r'```(?:bash\n)?(.*?)\n?```', generated_output, re.DOTALL | re.IGNORECASE)
        if match: cleaned_command = match.group(1).strip()
        else:
            cleaned_command = generated_output.replace('`', '').strip()
            if cleaned_command.lower().startswith("commande shell :"): cleaned_command = cleaned_command.split(":", 1)[1].strip()
        # Vérification finale
        if not cleaned_command or "CMD_ERROR" in cleaned_command or '\n' in cleaned_command:
            print(f"{COLOR_RED}Ollama n'a pas retourné une commande unique valide (Nettoyée: '{cleaned_command}').{COLOR_RESET}"); return None
        print(f"{COLOR_YELLOW}Commande nettoyée : '{cleaned_command}'{COLOR_RESET}"); return cleaned_command
    # --- Gestion des erreurs (simplifiée pour la lisibilité) ---
    except requests.exceptions.ConnectionError: print(f"\n{COLOR_RED}{COLOR_BOLD}Erreur connexion Ollama (Traduction).{COLOR_RESET}"); return None
    except requests.exceptions.Timeout: print(f"\n{COLOR_RED}{COLOR_BOLD}Timeout ({OLLAMA_TIMEOUT_TRANSLATE}s) Ollama (Traduction).{COLOR_RESET}"); return None
    except requests.exceptions.RequestException as e: print(f"\n{COLOR_RED}{COLOR_BOLD}Erreur requête Ollama (Traduction): {e}{COLOR_RESET}"); return None
    except Exception as e: print(f"\n{COLOR_RED}{COLOR_BOLD}Erreur inattendue (Traduction Ollama): {type(e).__name__}: {e}{COLOR_RESET}"); return None
