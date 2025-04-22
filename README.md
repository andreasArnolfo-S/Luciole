![image](./luciole.png)
# 🔥 Luciole – Assistant de Terminal Intelligent pour Linux & Cybersécurité

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Luciole** est un assistant de terminal intelligent pour les utilisateurs Linux (ou WSL), avec un focus sur la **cybersécurité** (Pentest, OSINT, etc.).  
✨ Propulsé par un **modèle de langage local** via [Ollama](https://ollama.com/), Luciole rend l'utilisation de votre terminal plus **intuitive, efficace et pédagogique**.

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

### 🧭 Deux Modes d'Interaction

#### 🔹 Mode Commande (`Commande >`)
- Exécutez vos commandes Linux habituelles.
- Luciole fournit :
  - ✅ **Analyse contextuelle des résultats** (explications, alternatives, sécurité).
  - 📌 **Réponses directes et concises** pour les commandes simples (`ls`, `pwd`, `echo`, etc.).
  - 📂 **Gestion intelligente des répertoires** (`cd` compris).

#### 🔹 Mode Langage Naturel (`Parlez >`)
- Exprimez vos intentions en français :
  - 🔧 **Traduction en commandes** : "compte les fichiers", "utilise sherlock sur user123".
  - 🧰 **Suggestions d'outils** : "quel outil pour scanner un site web ?"
  - 🛡️ **Confirmation avant exécution** de commandes sensibles (`rm`, `sudo`, etc.).

---

## ⚙️ Prérequis

- 🐍 **Python 3.x**
- 📦 Bibliothèque Python `requests` :
  ```bash
  pip install requests
  ```
- 🧠 **Ollama installé et fonctionnel** : [ollama.com](https://ollama.com/)
  - Téléchargez un modèle :
    ```bash
    ollama pull mistral
    ```
  - Lancez le service Ollama :
    ```bash
    ollama serve &
    ```

---

## 📦 Installation

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/<votre-utilisateur>/<nom-du-depot>.git
   cd <nom-du-depot>
   ```

2. Installez la dépendance :
   ```bash
   pip install requests
   ```

3. Assurez-vous qu’Ollama est bien **lancé et accessible sur `localhost:11434`** avec un modèle chargé.

---

## 🧑‍💻 Utilisation

1. Lancez Luciole :
   ```bash
   python3 luciole.py
   ```

2. Choisissez le modèle Ollama à utiliser (ex : `mistral`).

3. Interagissez avec Luciole :
   - 💻 **Mode Commande** (par défaut) : tapez vos commandes Linux habituelles.
   - 🗣 **Passer en Mode Naturel** : tapez `/mode` → prompt devient `Parlez >`.
   - 🔁 **Revenir en Mode Commande** : tapez à nouveau `/mode`.
   - ❌ **Quitter Luciole** : tapez `quitter`.

---

## 🛠 Configuration

- 📜 **Historique persistant** dans `~/.foxi_history` (navigable avec ↑ / ↓).
- 🌐 **API Ollama** configurée à :  
  `http://localhost:11434/api/generate`  
  *(modifiable dans le fichier Python si besoin)*.
- ⚙️ **Prompt système IA** personnalisable via la variable `SYSTEM_PROMPT` dans le code.

---

## 📄 Licence

Ce projet est distribué sous la licence **MIT**.  
📄 Voir le fichier [`LICENSE`](LICENSE) pour plus d’infos.

---

## ⚠️ Avertissement

L'interprétation des commandes en langage naturel repose sur un **modèle de langage (LLM)**.  
Bien que Luciole demande une confirmation pour les commandes sensibles, **restez vigilant** :  
- Ne lancez pas de commande sans la comprendre.
- Vérifiez toujours ce qui sera exécuté.
- 🧠 **Luciole est un assistant, pas un shell infaillible.**

---

## 💡 Astuce Bonus

🎨 Pour une expérience encore plus fun, pensez à utiliser **Oh My Zsh** ou un thème coloré dans votre terminal favori avec Luciole !

---

🛠️ *Projet maintenu avec passion. Contributions bienvenues !*
