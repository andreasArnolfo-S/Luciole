![alt text](./luciole.png)
# ✨ Luciole – Assistant de Terminal Intelligent v5 pour Linux & Cybersécurité

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Luciole** est un assistant de terminal intelligent et évolutif pour les utilisateurs Linux (ou WSL), avec un focus sur la **cybersécurité** (Pentest, OSINT, etc.).
🧠 Propulsé par un **modèle de langage local** via [Ollama](https://ollama.com/), Luciole vise à rendre l'utilisation de votre terminal plus **intuitive, efficace et pédagogique** grâce à une interface améliorée et des analyses contextuelles.

---

## 📚 Sommaire

- [🚀 Fonctionnalités Clés](#-fonctionnalités-clés)
- [⚙️ Prérequis](#️-prérequis)
- [📦 Installation](#-installation)
- [🧑‍💻 Utilisation](#-utilisation)
- [🛠 Configuration](#-configuration)
- [📄 Licence](#-licence)
- [⚠️ Avertissement](#️-avertissement)

---

## 🚀 Fonctionnalités Clés

### 🧭 Deux Modes d'Interaction Principaux

Luciole fonctionne selon deux modes distincts :

#### 1. Mode Commande (`💻 Commande >`)
* Exécutez vos commandes Linux habituelles.
* Luciole fournit ensuite une analyse contextuelle :
    * 🧠 **Analyse basée sur l'Historique** : Tient compte des dernières commandes exécutées.
    * 🛡️ **Analyse Spécialisée Sécurité** : Détecte les outils de sécurité courants (`nmap`, `gobuster`, `whatweb`...) et demande à l'IA une analyse plus poussée (résumé des faits, options utilisées, suggestions d'étapes suivantes pertinentes, CVEs potentiels).
    * ✅ **Explication claire** des succès ou erreurs.
    * 💨 **Réponses directes** pour les commandes très simples (`pwd`, `whoami`...).
    * 📂 **Gestion intelligente** du changement de répertoire (`cd`).

#### 2. Mode Langage Naturel (`🗣️ Parlez >`)
* Exprimez vos intentions en français :
    * 💬 **Traduction Contextuelle** : "compte les mots dans ce fichier", "utilise nikto sur le port trouvé avant". L'historique est utilisé pour comprendre les références.
    * 💡 **Génération de Commandes** : Pour des actions spécifiques ou l'utilisation d'outils particuliers.
    * 🛡️ **Confirmation avant exécution** de commandes jugées dangereuses (`rm`, `sudo`...).
    * 📊 **Analyse du Résultat** : Après exécution, le résultat est analysé comme en Mode Commande.

### ✨ Fonctionnalités Additionnelles

* **Interface Améliorée (`rich`)** : Utilisation de couleurs, styles (gras), règles de séparation et émojis pour une meilleure lisibilité.
* **Spinner d'Attente** : Un indicateur visuel (spinner) s'affiche pendant que Luciole communique avec Ollama.
* **Suggestion d'Outils (`/suggest_tools`)** : Demandez des recommandations d'outils pour une tâche spécifique (ex: `/suggest_tools chercher des emails sur un site`).
* **Aide Intégrée (`/help`)** : Affiche un résumé des commandes et des modes.
* **Historique de Commandes** : Navigation facile avec les flèches Haut/Bas (via `readline`).
* **Conscience du Contexte Court Terme** : Mémorise les 3 dernières interactions (commande, stdout, stderr) pour améliorer la pertinence des réponses d'Ollama.

---

## ⚙️ Prérequis

* 🐍 **Python 3.x** (testé avec 3.10+)
* 📦 Bibliothèques Python `requests` et `rich` :
    ```bash
    # Idéalement dans un environnement virtuel
    pip install requests rich
    # Ou utiliser le fichier requirements.txt fourni
    pip install -r requirements.txt
    ```
* 🧠 **Ollama installé et fonctionnel** : [ollama.com](https://ollama.com/)
    * Téléchargez au moins un modèle (le défaut actuel est `codellama`, mais `mistral` est une bonne alternative rapide) :
        ```bash
        ollama pull codellama
        ollama pull mistral
        ```
    * Assurez-vous que le service Ollama tourne (souvent lancé automatiquement, sinon `ollama serve &`).

---

## 📦 Installation

1.  Clonez le dépôt (si ce n'est pas déjà fait) :
    ```bash
    git clone [https://github.com/](https://github.com/)<votre-utilisateur>/Luciole.git # Adaptez l'URL
    cd Luciole
    ```
2.  (Recommandé) Créez et activez un environnement virtuel Python :
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    *(Note : Si l'activation ne modifie pas correctement votre `PATH` (vérifiez avec `which python3`), vous devrez lancer Luciole avec le chemin complet : `venv/bin/python3 main.py`)*
3.  Installez les dépendances :
    ```bash
    # Assurez-vous d'utiliser le pip du venv si l'activation est partielle
    python3 -m pip install -r requirements.txt
    ```
4.  Assurez-vous qu’Ollama est bien **lancé et accessible sur `http://localhost:11434`** avec au moins un modèle téléchargé (ex: `codellama` ou `mistral`).

---

## 🧑‍💻 Utilisation

1.  Lancez Luciole (depuis le dossier du projet, avec le venv activé si possible) :
    ```bash
    # Si l'activation du venv fonctionne correctement
    python3 main.py
    # OU si l'activation du venv a des problèmes de PATH (vu sur Kali/WSL)
    ./venv/bin/python3 main.py
    ```
2.  Choisissez le modèle Ollama à utiliser lorsque demandé (appuyez sur Entrée pour le défaut, actuellement `codellama`).

3.  Interagissez avec Luciole :
    * 💻 **Mode Commande** (par défaut) : Tapez vos commandes Linux. Observez le spinner pendant l'analyse.
    * 🗣️ **Passer en Mode Naturel** : Tapez `/mode` → le prompt change (`🗣️ Parlez >`). Tapez votre demande en français. Observez le spinner pendant la traduction et l'analyse.
    * 🔁 **Revenir en Mode Commande** : Tapez `/mode` à nouveau.
    * 💡 **Suggestion d'Outils** : Tapez `/suggest_tools [description de la tâche]`.
    * ❓ **Obtenir de l'Aide** : Tapez `/help`.
    * ❌ **Quitter Luciole** : Tapez `quitter`.

---

## 🛠 Configuration

* **Fichier `config.py` :**
    * `DEFAULT_MODEL` : Modèle Ollama utilisé par défaut (actuellement "codellama").
    * `OLLAMA_API_URL` : Adresse du serveur Ollama.
    * `SYSTEM_PROMPT` : Instructions globales pour la personnalité et les capacités de Luciole.
    * `SECURITY_TOOLS` : Liste des commandes reconnues comme outils de sécurité pour l'analyse spécialisée.
    * `DANGEROUS_KEYWORDS` : Liste des commandes nécessitant une confirmation en mode naturel.
    * Constantes de couleurs (utilisées pour le prompt `input()`).
* **Fichier `main.py` :**
    * `conversation_history = deque(maxlen=3)` : Modifiez `maxlen` pour changer la taille de l'historique de contexte.
* **Historique Readline** : Sauvegardé dans `~/.foxi_history` (chemin défini dans `config.py`).

*(Une future version pourrait utiliser un fichier de configuration externe pour plus de facilité.)*

---

## 📄 Licence

Ce projet est distribué sous la licence **MIT**.
📄 Voir le fichier [`LICENSE`](LICENSE) pour plus d’infos.

---

## ⚠️ Avertissement

L'interprétation et la génération de commandes reposent sur un **modèle de langage (LLM)**. Les analyses (surtout sécurité) et les suggestions d'outils sont des **aides** et peuvent contenir des **imprécisions ou des hallucinations**.
Bien que Luciole demande une confirmation pour les commandes dangereuses, **restez TOUJOURS vigilant** :
* Ne lancez pas de commande sans la comprendre.
* Vérifiez toujours ce qui sera exécuté.
* Vérifiez manuellement les analyses et suggestions de l'IA.
* 🧠 **Luciole est un assistant, pas un expert infaillible.** Vous restez responsable de vos actions.

---

🛠️ *Projet maintenu avec passion - Contributions et suggestions bienvenues !*