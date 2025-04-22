# -*- coding: utf-8 -*-
# ollama_client.py : Fonctions pour interagir avec l'API Ollama

import requests
import sys
import re
import json
from config import (
    OLLAMA_API_URL, SYSTEM_PROMPT, OLLAMA_TIMEOUT_ANALYSIS, OLLAMA_TIMEOUT_TRANSLATE,
    COLOR_YELLOW, COLOR_RED, COLOR_RESET, LS_COMMAND, COLOR_BLUE, COLOR_BOLD 
)

# --- MODIFICATION : get_ollama_analysis pour gérer le streaming ---
def get_ollama_analysis(command, stdout, stderr, model_name, prompt_type="detailed"):
    """ Interroge l'API Ollama locale pour analyser la sortie d'une commande (AVEC STREAMING). """
    stdout_str = stdout if stdout is not None else "(Erreur lors de la récupération de stdout)"
    stderr_str = stderr if stderr is not None else "(Erreur lors de la récupération de stderr)"
    prompt = ""

    # (Le code pour déterminer le prompt reste le même)
    if prompt_type == "simple_ls":
         prompt = f"""La commande `{LS_COMMAND}` (ou une variante) a retourné :

{stdout_str.strip()}

Décris cette sortie en une seule phrase très simple et naturelle en français, comme si tu regardais dans le dossier. Commence par "Dans ce dossier, il y a" ou similaire. Ne donne que cette phrase. Pas d'alternatives.
"""
    else: # prompt_type == "detailed" ou autre
         prompt = f"""The following command was executed:
`{command}`

Standard Output:

{stdout_str.strip() if stdout_str else "(none)"}


Standard Error:

{stderr_str.strip() if stderr_str else "(none)"}


Based on your role as Foxi (Linux & cybersecurity expert), analyze this. Explain the result/error simply. Suggest relevant follow-up commands or security considerations if applicable (especially for errors or tools like nmap). Keep it brief for simple successes. Provide alternatives if relevant.
"""

    payload = {
        "model": model_name,
        "system": SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": True # <-- MODIFIÉ : Activer le streaming côté Ollama
    }

    analysis_content = "" # Pour stocker le contenu si besoin, mais surtout pour vérifier si on a reçu qqchose
    error_occurred = False

    try:
        # --- AJOUT : Message d'attente ---
        print(f"\n{COLOR_YELLOW}Analyse en cours...{COLOR_RESET}", flush=True)

        # --- MODIFIÉ : Appel requests avec stream=True ---
        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT_ANALYSIS, # Timeout pour la connexion initiale
            stream=True # <-- MODIFIÉ : Activer le streaming côté client requests
        )
        response.raise_for_status() # Vérifie les erreurs HTTP (4xx, 5xx) dès le début

        # --- MODIFIÉ : Traitement de la réponse en streaming ---
        print(f"{COLOR_BLUE}", end='') # Commence à écrire en bleu pour l'analyse
        for line in response.iter_lines():
            if line:
                try:
                    decoded_line = line.decode('utf-8')
                    data = json.loads(decoded_line)
                    chunk = data.get("response", "")
                    analysis_content += chunk # Accumule le contenu
                    print(chunk, end='', flush=True) # Affiche le morceau reçu immédiatement

                    # Vérifie si c'est le dernier chunk
                    if data.get("done"):
                        break # Sortir de la boucle une fois terminé
                except json.JSONDecodeError:
                    print(f"\n{COLOR_RED}Erreur de décodage JSON sur une ligne du stream.{COLOR_RESET}")
                    # Continue d'essayer de lire les lignes suivantes si possible
                except Exception as e:
                    print(f"\n{COLOR_RED}Erreur pendant le traitement du stream: {e}{COLOR_RESET}")
                    error_occurred = True
                    break # Sortir en cas d'autre erreur de stream

        print(f"{COLOR_RESET}") # Remet la couleur par défaut à la fin du stream

        if not error_occurred:
             # --- AJOUT : Message de fin (optionnel, car le prompt suivant apparaît) ---
             # print(f"{COLOR_YELLOW}Analyse terminée.{COLOR_RESET}")
             pass # On peut omettre le message de fin pour ne pas surcharger

        # Si tout s'est bien passé et qu'on a reçu du contenu, retourne None pour indiquer à main.py de ne rien afficher de plus
        # S'il n'y a eu aucun contenu (étrange mais possible), on retourne une chaîne vide pour que main.py affiche qqc
        return None if analysis_content else ""


    # --- Gestion des erreurs (largement inchangée, mais s'applique à la connexion initiale ou aux erreurs de stream) ---
    except requests.exceptions.ConnectionError:
        err_msg = (f"\n{COLOR_RED}{COLOR_BOLD}Erreur : Impossible de se connecter au serveur Ollama.{COLOR_RESET}\n"
                   f"{COLOR_RED}Vérifiez qu'Ollama est lancé ('ollama run {model_name}') et accessible à {OLLAMA_API_URL}{COLOR_RESET}")
        print(err_msg) # Affiche l'erreur ici directement
        return err_msg # Retourne le message pour potentiellement l'afficher à nouveau dans main.py (facultatif)
    except requests.exceptions.Timeout:
        err_msg = f"\n{COLOR_RED}{COLOR_BOLD}Erreur : Timeout ({OLLAMA_TIMEOUT_ANALYSIS}s) lors de la connexion initiale à Ollama pour l'analyse.{COLOR_RESET}"
        print(err_msg)
        return err_msg
    except requests.exceptions.RequestException as e:
        err_msg = f"\n{COLOR_RED}{COLOR_BOLD}Erreur lors de la requête d'analyse Ollama : {e}{COLOR_RESET}"
        print(err_msg)
        # Essayer d'afficher les détails de l'erreur si possible
        try:
            if e.response is not None:
                error_details = e.response.json()
                print(f"{COLOR_RED}Détails: {json.dumps(error_details)}{COLOR_RESET}")
                err_msg += f"\nDétails: {json.dumps(error_details)}"
        except: pass
        return err_msg
    # Capture d'autres erreurs potentielles pendant le stream qui n'ont pas été gérées dans la boucle
    except Exception as e:
        err_msg = f"\n{COLOR_RED}{COLOR_BOLD}Erreur inattendue lors de l'analyse Ollama ({type(e).__name__}): {e}{COLOR_RESET}"
        print(err_msg)
        return err_msg

# --- MODIFICATION : get_command_from_natural_language pour ajouter le message d'attente ---
def get_command_from_natural_language(natural_language_input, model_name):
    """ Demande à Ollama de traduire une phrase en commande shell (sans streaming). """
    prompt = f"""Traduis la requête utilisateur suivante en UNE SEULE commande shell Linux standard et exécutable. Réponds UNIQUEMENT avec la commande exacte, sans explication, formatage (comme ```), salutation, ou texte supplémentaire. Si la requête est ambiguë, dangereuse, nécessite plusieurs étapes, ou si tu ne peux pas la traduire en une commande shell unique et raisonnable, réponds exactement avec le mot 'CMD_ERROR'.

Requête utilisateur : "{natural_language_input}"

Commande shell :"""

    payload = {
        "model": model_name,
        "system": SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": False, # Garder False ici, pas besoin de streamer une commande courte
    }
    try:
        # --- AJOUT : Message d'attente ---
        print(f"\n{COLOR_YELLOW}Traduction en cours...{COLOR_RESET}", flush=True)

        response = requests.post(OLLAMA_API_URL, json=payload, timeout=OLLAMA_TIMEOUT_TRANSLATE)
        response.raise_for_status()
        data = response.json()
        generated_output = data.get("response", "").strip()
        # --- AJOUT : Message de réception (optionnel mais utile) ---
        print(f"{COLOR_YELLOW}Traduction reçue (brute) : '{generated_output}'{COLOR_RESET}")

        # (Le code de nettoyage reste le même)
        match = re.search(r'```(?:bash\n)?(.*?)\n?```', generated_output, re.DOTALL | re.IGNORECASE)
        if match:
            cleaned_command = match.group(1).strip()
        else:
            cleaned_command = generated_output.replace('`', '').strip()
            if cleaned_command.lower().startswith("commande shell :"):
                 cleaned_command = cleaned_command.split(":", 1)[1].strip()

        if not cleaned_command or "CMD_ERROR" in cleaned_command or '\n' in cleaned_command:
            print(f"{COLOR_RED}Ollama n'a pas retourné une commande unique valide (Nettoyée: '{cleaned_command}').{COLOR_RESET}")
            return None

        print(f"{COLOR_YELLOW}Commande nettoyée : '{cleaned_command}'{COLOR_RESET}")
        return cleaned_command

    # --- Gestion des erreurs (inchangée, mais les messages sont en gras/rouge) ---
    except requests.exceptions.ConnectionError:
        print(f"\n{COLOR_RED}{COLOR_BOLD}Erreur de connexion à Ollama pour la traduction.{COLOR_RESET}")
        return None
    except requests.exceptions.Timeout:
        print(f"\n{COLOR_RED}{COLOR_BOLD}Timeout ({OLLAMA_TIMEOUT_TRANSLATE}s) lors de la traduction par Ollama.{COLOR_RESET}")
        return None
    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response else "N/A"
        print(f"\n{COLOR_RED}{COLOR_BOLD}Erreur de requête Ollama lors de la traduction ({status_code}): {e}{COLOR_RESET}")
        if e.response is not None:
            try:
                error_details = e.response.json()
                print(f"{COLOR_RED}Détails de l'erreur Ollama: {error_details}{COLOR_RESET}")
            except json.JSONDecodeError:
                print(f"{COLOR_RED}Le corps de la réponse d'erreur n'est pas du JSON valide.{COLOR_RESET}")
        return None
    except Exception as e:
        print(f"\n{COLOR_RED}{COLOR_BOLD}Erreur inattendue lors de la traduction ({type(e).__name__}): {e}{COLOR_RESET}")
        return None