# -*- coding: utf-8 -*-
# config.py : Constantes et configuration pour Luciole

import os

# --- Constantes pour les couleurs ANSI ---
COLOR_RESET = "\033[0m"
COLOR_BLUE = "\033[94m"    # Pour l'analyse Ollama / réponses directes
COLOR_GREEN = "\033[92m"   # Pour stdout et le prompt
COLOR_YELLOW = "\033[93m"  # Pour les messages d'exécution / infos
COLOR_RED = "\033[91m"      # Pour stderr et les erreurs
COLOR_CYAN = "\033[96m"     # Pour les en-têtes de section / prompt dossier
COLOR_MAGENTA = "\033[95m" # Pour le prompt mode naturel
COLOR_BOLD = "\033[1m"

# --- Configuration de l'historique ---
HISTFILE = os.path.expanduser("~/.foxi_history") # Chemin du fichier d'historique
HISTSIZE = 1000                                  # Nombre maximum de lignes à conserver

# --- Configuration Ollama ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "codellama"
OLLAMA_TIMEOUT_ANALYSIS = 90  # Timeout pour les requêtes d'analyse (secondes)
OLLAMA_TIMEOUT_TRANSLATE = 60 # Timeout pour les requêtes de traduction (secondes)

# --- Prompt Système pour Ollama ---
SYSTEM_PROMPT = """Tu es Luciole, un assistant expert en ligne de commande Linux et spécialisé en cybersécurité. Ton but est d'aider l'utilisateur en tenant compte de l'historique de la conversation fourni.
- En mode commande, analyse les résultats de la commande la plus récente à la lumière des interactions précédentes. Explique-les clairement (surtout les erreurs), et suggère des commandes alternatives pertinentes ou des commandes de suivi basées sur le contexte. Pour les outils de sécurité comme nmap, essaie d'identifier les informations critiques. Sois concis pour les commandes très simples réussies.
- En mode naturel, traduis la demande de l'utilisateur en une commande shell Linux unique et exécutable, en utilisant l'historique pour résoudre les références (ex: 'le fichier précédent'). Si la demande mentionne un outil spécifique, génère la commande pour cet outil. Réponds UNIQUEMENT avec la commande ou 'CMD_ERROR' si tu ne peux pas ou si c'est ambigu/dangereux.
Sois précis, technique et fiable."""

# --- Mots-clés pour commandes dangereuses ---
# (Préfixés ou contenant des espaces pour éviter les faux positifs, ex: 'arm' != 'rm ')
DANGEROUS_KEYWORDS = [
    'rm ', 'mv ', 'dd ', 'sudo ', 'chmod ', 'chown ', ' mkfs',
    ':(){:|:&};:', # Fork bomb
    ' > /dev/sd', # Écraser un disque
    ' > /dev/null' # Peut être dangereux si mal utilisé avec des commandes critiques
]

# --- Commandes Simples avec gestion directe ---
SIMPLE_COMMANDS = ["pwd", "whoami"]
LS_COMMAND = "ls" # Spécifiquement pour le prompt simple
ECHO_XXD_PIPE = "echo | xxd -r -p" # Détection de cette séquence spécifique

# --- AJOUT : Liste des commandes d'outils de sécurité courants ---
# (À enrichir au besoin)
SECURITY_TOOLS = [
    'nmap', 'masscan', 'gobuster', 'feroxbuster', 'dirb', 'wfuzz',
    'sqlmap', 'nikto', 'whatweb', 'wafw00f',
    'msfconsole', 'msfvenom',
    'hydra', 'john', 'hashcat',
    'subfinder', 'assetfinder', 'amass', 'httpx', 'nuclei',
    'searchsploit', 'enum4linux', 'smbclient', 'smbmap', 'rpcclient',
    'aircrack-ng', 'airodump-ng', 'reaver', 'bully',
    'burpsuite', 'zaproxy', # Moins CLI mais contextuellement utiles
    'whois', 'dnsrecon', 'fierce',
    'metagoofil', 'sherlock', # OSINT
    # Ajouter d'autres outils pertinents...
]
# --- FIN AJOUT ---