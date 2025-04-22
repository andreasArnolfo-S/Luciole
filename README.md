# Luciole : Assistant de Terminal Intelligent Linux & Cybersécurité

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) Luciole est un assistant de terminal intelligent conçu pour les utilisateurs Linux (ou WSL), en particulier ceux intéressés par la cybersécurité (pentest, OSINT). Propulsé par un modèle de langage local via Ollama, Luciole transforme votre interaction avec la ligne de commande pour la rendre plus efficace, informative et intuitive.

## Fonctionnalités Clés

* **Deux Modes d'Interaction :**
    * **Mode Commande (`Commande >`) :** Exécutez vos commandes Linux habituelles. Luciole fournit :
        * Une analyse contextuelle des résultats par l'IA (explication simple, alternatives, considérations de sécurité pour certains outils comme `nmap`).
        * Des réponses directes et concises pour les commandes simples réussies (`ls`, `pwd`, `whoami`, `echo ... | xxd -r -p`).
        * Gestion correcte de la commande `cd`.
    * **Mode Langage Naturel (`Parlez >`) :** Communiquez vos intentions en français.
        * **Traduction en Commandes :** Demandez une action ("compte les fichiers", "utilise sherlock sur user123") et Luciole tente de générer la commande correspondante.
        * **Suggestion d'Outils :** Demandez quel outil utiliser pour une tâche OSINT/Pentest ("quel outil pour trouver les sous-domaines ?") et Luciole vous suggérera des options avec exemples.
        * **Confirmation de Sécurité :** Demande votre accord avant d'exécuter des commandes générées jugées potentiellement dangereuses (`rm`, `sudo`...).

* **Confort d'Utilisation :**
    * **Historique des commandes** persistant (`~/.foxi_history`) avec navigation via les flèches Haut/Bas.
    * Sortie **colorée** pour une meilleure lisibilité.
    * Affichage du répertoire courant dans le prompt.

* **Technologie Locale :** Utilise **Ollama** pour faire tourner les modèles de langage (comme Mistral, Llama 3) **localement** sur votre machine.

## Prérequis

* **Python 3.x**
* La bibliothèque Python `requests` : `pip install requests`
* **Ollama installé et fonctionnel** : [Voir le site officiel d'Ollama](https://ollama.com/)
    * Au moins un modèle téléchargé (ex: `ollama pull mistral`)
    * Le service Ollama doit être **lancé** (ex: `ollama serve &` ou en lançant `ollama run mistral` dans un autre terminal). Luciole s'attend à le trouver sur `http://localhost:11434`.

## Installation

1.  **Clonez le dépôt (ou téléchargez le fichier `Luciole.py`) :**
    ```bash
    git clone <URL_de_votre_depot_github>
    cd <nom_du_dossier_du_depot>
    ```
2.  **Installez la dépendance Python :**
    ```bash
    pip install requests
    # ou
    pip3 install requests
    ```
3.  **Assurez-vous qu'Ollama est installé et lancé** avec un modèle disponible (voir Prérequis).

## Utilisation

1.  **Lancez Luciole :**
    ```bash
    python3 Luciole.py
    ```
2.  **Choisissez le modèle Ollama** que vous souhaitez utiliser (ex: `mistral`).
3.  **Interagissez :**
    * **Mode Commande (par défaut) :** Tapez directement vos commandes Linux. Utilisez ↑/↓ pour l'historique.
    * **Passer en Mode Naturel :** Tapez `/mode` et validez. Le prompt devient `Parlez >`.
    * **Mode Naturel :**
        * Pour exécuter une action : Décrivez-la (ex: `affiche le contenu du fichier config.txt`).
        * Pour obtenir des suggestions : Posez une question (ex: `quel outil pour scanner un site web ?`).
    * **Revenir en Mode Commande :** Tapez `/mode` et validez.
    * **Quitter :** Tapez `quitter` et validez.

## Configuration

* **Historique :** Le fichier d'historique est sauvegardé dans `~/.foxi_history`.
* **URL Ollama :** L'URL est définie dans le code (`ollama_api_url = "http://localhost:11434/api/generate"`). Modifiez-la si votre serveur Ollama tourne ailleurs.
* **Prompt Système :** Le comportement de l'IA est guidé par `SYSTEM_PROMPT` dans le code. Vous pouvez l'ajuster pour expérimenter.

## Licence

Ce projet est distribué sous la licence [Nom de la Licence - ex: MIT]. Voir le fichier `LICENSE` pour plus de détails.

*(**Note :** N'oubliez pas de choisir une licence - MIT ou Apache 2.0 sont de bons choix - et d'ajouter le fichier `LICENSE` correspondant dans votre dépôt !)*

## Avertissement

L'utilisation du mode langage naturel pour générer et exécuter des commandes repose sur un modèle de langage (LLM). Bien que des garde-fous soient en place (demande de confirmation), les LLMs peuvent parfois mal interpréter les demandes ou générer des commandes inattendues ou incorrectes. **Utilisez cette fonctionnalité avec prudence**, en particulier pour les commandes qui pourraient modifier ou supprimer des fichiers, ou avoir des impacts sur la sécurité. Vérifiez toujours la commande suggérée avant de confirmer son exécution si vous avez le moindre doute. Cet outil est fourni à titre expérimental et éducatif.

---