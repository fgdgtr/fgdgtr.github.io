# ⚡ CHECKLIST SETUP RAPIDE (10 min)

## ✅ AVANT DE COMMENCER

- [ ] Compte GitHub (gratuit sur github.com)
- [ ] Accès à thuillier.kevin10@gmail.com (pour envoyer les rapports)
- [ ] L'app ne doit PAS être arrêtée (elle lit les données Firebase)

---

## 🚀 PHASE 1: GITHUB (2 min)

- [ ] Créer repo `auem-rack-reports` sur GitHub
- [ ] Uploader les 3 fichiers:
  - [ ] `script_rapport.py` (à la racine)
  - [ ] `export.yml` (dans `.github/workflows/`)
  - [ ] `README.md` (à la racine)

---

## 🔐 PHASE 2: GMAIL (3 min)

- [ ] Aller sur myaccount.google.com
- [ ] Activer 2-Step Verification (si pas déjà fait)
- [ ] Générer un "App Password" pour Gmail
- [ ] Copier le mot de passe (16 caractères)

**Mot de passe: `_________________`** ← À copier ici

---

## 🔧 PHASE 3: SECRETS GITHUB (3 min)

Dans Settings → Secrets and variables → Actions, ajouter:

- [ ] **FIREBASE_URL**
  ```
  https://auem-rac-default-rtdb.europe-west1.firebasedatabase.app/retour.json
  ```

- [ ] **SMTP_USER**
  ```
  thuillier.kevin10@gmail.com
  ```

- [ ] **SMTP_PASSWORD**
  ```
  [Coller le mot de passe d'app Gmail]
  ```

- [ ] **RAPPORT_EMAIL**
  ```
  axefoxe8592@gmail.com
  ```

---

## 🧪 PHASE 4: TEST (2 min)

- [ ] Aller dans Actions → Rapport Hebdomadaire Rack
- [ ] Clicker "Run workflow"
- [ ] Attendre 2 min
- [ ] Vérifier que c'est ✅ vert
- [ ] Vérifier mail reçu à axefoxe8592@gmail.com

---

## ✨ C'EST BON!

Chaque **vendredi à 17h**, tu reçois automatiquement un PDF!

**Pour changer le destinataire:**
- Settings → Secrets → RAPPORT_EMAIL → Edit → Nouvelle adresse

---

## 🆘 SI ÇA NE MARCHE PAS

1. Actions → dernière run (elle aura une ❌ rouge)
2. Clicker dessus
3. "generate-report"
4. Scroll pour voir le message d'erreur rouge
5. Si c'est "Authentication failed" → Mot de passe Gmail mauvais
6. Si c'est "Firebase connection error" → URL Firebase incorrecte
7. Si pas de mail → Vérifier le dossier Spam

Viens me montrer l'erreur exacte et je corrige!

---

**Questions?** → Demande-moi!
