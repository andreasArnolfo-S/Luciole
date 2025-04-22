# -*- coding: utf-8 -*-
# shell_utils.py : Fonctions utilitaires pour l'interaction shell

import subprocess
import shlex
import os
import re
from config import COLOR_YELLOW, COLOR_RED, COLOR_RESET

def has_shell_operators(command_string):
    """ Vérifie si la commande contient des opérateurs nécessitant shell=True. """
    # Opérateurs: | > < >> & ; && || $ ` ( ) { } [ ] \ * ? # ~ = %
    # Simplifié pour les cas courants, mais pourrait être étendu
    return bool(re.search(r'[|><;&$`(){}[\]\\*?#~=]', command_string))

def execute_command(command_string):
    """
    Exécute une commande shell, en utilisant shell=True si des opérateurs
    spéciaux sont détectés, sinon utilise shell=False.
    Retourne (stdout, stderr). En cas d'erreur d'exécution majeure, stdout est None.
    """
    print(f"{COLOR_YELLOW}Tentative d'exécution : {command_string}{COLOR_RESET}")
    stdout_res, stderr_res = None, None
    try:
        if has_shell_operators(command_string):
            print(f"{COLOR_YELLOW}Opérateurs shell détectés. Utilisation de shell=True.{COLOR_RESET}")
            # Utilisation de /bin/bash explicitement pour une meilleure cohérence
            shell_executable = os.getenv('SHELL', '/bin/bash')
            result = subprocess.run(
                command_string, shell=True, capture_output=True, text=True,
                check=False, encoding='utf-8', errors='replace',
                executable=shell_executable
            )
        else:
            # shlex.split gère correctement les espaces et les guillemets
            args = shlex.split(command_string)
            # Vérifier si la commande est vide après split (ex: juste des espaces)
            if not args:
                print(f"{COLOR_YELLOW}Commande vide après séparation, rien à exécuter.{COLOR_RESET}")
                return "", "" # Retourner des chaînes vides pour éviter les erreurs None plus tard

            print(f"{COLOR_YELLOW}Exécution via arguments séparés (shell=False).{COLOR_RESET}")
            result = subprocess.run(
                args, shell=False, capture_output=True, text=True,
                check=False, encoding='utf-8', errors='replace'
            )
        stdout_res = result.stdout
        stderr_res = result.stderr
    except FileNotFoundError as e:
        # Cas où la commande elle-même ou le shell n'est pas trouvé
        err_msg = f"Commande, programme ou shell introuvable : {e}"
        print(f"{COLOR_RED}Erreur: {err_msg}{COLOR_RESET}")
        stderr_res = err_msg # Mettre l'erreur dans stderr pour l'analyse LLM
    except Exception as e:
        # Autres erreurs potentielles (permissions, etc.)
        err_msg = f"Erreur inattendue lors de l'exécution ({type(e).__name__}): {e}"
        print(f"{COLOR_RED}Erreur: {err_msg}{COLOR_RESET}")
        stderr_res = err_msg # Mettre l'erreur dans stderr

    return stdout_res, stderr_res

def change_directory(target_dir):
    """
    Tente de changer le répertoire courant.
    Retourne True si réussi, False sinon.
    """
    original_dir = os.getcwd()
    try:
        # Gérer le cas "cd" sans argument -> retour au dossier home
        if not target_dir or target_dir == "~":
            expanded_target_dir = os.path.expanduser("~")
        else:
            expanded_target_dir = os.path.expanduser(target_dir)

        os.chdir(expanded_target_dir)
        new_dir = os.getcwd()
        if original_dir != new_dir: # Afficher uniquement si le répertoire a changé
            print(f"{COLOR_YELLOW}Nouveau répertoire : {new_dir}{COLOR_RESET}")
        return True
    except FileNotFoundError:
        print(f"{COLOR_RED}Erreur: Le dossier '{expanded_target_dir}' n'existe pas.{COLOR_RESET}")
        return False
    except PermissionError:
        print(f"{COLOR_RED}Erreur: Permission refusée pour accéder au dossier '{expanded_target_dir}'.{COLOR_RESET}")
        return False
    except NotADirectoryError:
         print(f"{COLOR_RED}Erreur: '{expanded_target_dir}' n'est pas un dossier.{COLOR_RESET}")
         return False
    except Exception as e:
        print(f"{COLOR_RED}Erreur inattendue avec 'cd': {e}{COLOR_RESET}")
        return False