# 📊 AUEM Rack - Rapports Automatiques

Système d'export automatique des données du rack en PDF, chaque vendredi à 17h.

---

## 📋 TABLE DES MATIÈRES

1. [Setup initial (5 min)](#setup-initial)
2. [Configuration Gmail (3 min)](#configuration-gmail)
3. [Configuration GitHub (3 min)](#configuration-github)
4. [Tester le système](#tester)
5. [Modifier le destinataire](#modifier-destinataire)

---

## 🚀 SETUP INITIAL

### Étape 1: Créer un repo GitHub

1. Va sur [github.com](https://github.com)
2. Clique "**New repository**"
3. **Repository name**: `auem-rack-reports`
4. **Description**: `Rapports automatiques rack AUEM`
5. **Public** (cocher) - permet à GitHub Actions de fonctionner
6. Clique "**Create repository**"

### Étape 2: Ajouter les fichiers

1. Dans ton repo, va sur "**Add file**" → "**Upload files**"
2. Upload ces 3 fichiers:
   - `script_rapport.py`
   - `export.yml` (mettre dans `.github/workflows/`)
   - `README.md`

**Ou** clone le repo et ajoute les fichiers en local.

---

## 🔐 CONFIGURATION GMAIL

Tu vas donner à GitHub un **mot de passe spécial Gmail** (pas ton vrai mot de passe).

### Créer un "App Password" Gmail

1. Va sur [myaccount.google.com](https://myaccount.google.com)
2. Clique "**Security**" (à gauche)
3. Active **2-Step Verification** si ce n'est pas fait
   - Clique "2-Step Verification"
   - Suit les étapes
4. Une fois 2FA activé, reviens à Security
5. Tu verras maintenant "**App passwords**"
6. Clique "**App passwords**"
7. Sélectionne:
   - App: **Mail**
   - Device: **Windows Computer** (ou ton OS)
8. Clique "**Generate**"
9. **Copie le mot de passe** (16 caractères)

⚠️ **IMPORTANT**: C'est un mot de passe unique pour cette app, pas ton vrai mot de passe Gmail!

---

## 🔧 CONFIGURATION GITHUB

### Ajouter les Secrets GitHub

1. Va dans ton repo GitHub
2. **Settings** (onglet en haut)
3. À gauche → "**Secrets and variables**" → "**Actions**"
4. Clique "**New repository secret**"

**Ajoute ces 4 secrets** (un par un):

| Nom | Valeur | Exemple |
|-----|--------|---------|
| `FIREBASE_URL` | URL Firebase du rack retour | `https://auem-rac-default-rtdb.europe-west1.firebasedatabase.app/retour.json` |
| `SMTP_USER` | Ton email Gmail | `thuillier.kevin10@gmail.com` |
| `SMTP_PASSWORD` | Le mot de passe d'app généré | `abcd efgh ijkl mnop` |
| `RAPPORT_EMAIL` | Email destinataire | `axefoxe8592@gmail.com` |

**Comment ajouter un secret:**
1. Clique "**New repository secret**"
2. **Name**: (ex: `FIREBASE_URL`)
3. **Secret**: (la valeur)
4. Clique "**Add secret**"

**Répète pour les 4.**

---

## 🧪 TESTER LE SYSTÈME

### Test manuel (avant vendredi)

1. Va dans ton repo → onglet **"Actions"**
2. À gauche, clique "**📊 Rapport Hebdomadaire Rack**"
3. À droite, clique "**Run workflow**"
4. Clique "**Run workflow**"
5. Attends 1-2 minutes
6. Tu dois voir ✅ vert

**Vérifications:**
- ✅ L'action est **verte** (success)
- ✅ Tu as reçu un mail à `axefoxe8592@gmail.com`
- ✅ Le PDF est en pièce jointe

**Si ❌ rouge (erreur):**
- Clique sur l'action rouge
- Clique "**generate-report**"
- Scroll vers le bas pour voir l'erreur
- Corrige le secret qui pose problème

### Test du planning

Le rapport s'envoie **chaque vendredi à 17h** (heure UTC+0).

Si tu es en France (UTC+1 en hiver, UTC+2 en été), ça sera:
- **16h** en hiver
- **15h** en été

(Tu peux changer le timing dans `export.yml` si tu veux)

---

## ✏️ MODIFIER LE DESTINATAIRE

**Super facile - pas de code à toucher!**

### Changer l'email qui reçoit le rapport

1. Va dans ton repo → **Settings**
2. "**Secrets and variables**" → "**Actions**"
3. Cherche `RAPPORT_EMAIL`
4. Clique sur le petit crayon ✏️
5. Change l'email (ex: `directeur@auem.fr`)
6. Clique "**Update secret**"

✅ **C'est tout!** Le prochain rapport ira à ce nouvel email.

### Ajouter un 2e destinataire (optionnel)

Si tu veux envoyer à 2 emails:
1. Édite `script_rapport.py`
2. À la fin, change:
```python
send_email(pdf_file, RAPPORT_EMAIL)
```

En:
```python
send_email(pdf_file, RAPPORT_EMAIL)
send_email(pdf_file, 'deuxieme.email@auem.fr')
```

3. Commit et push
4. Done!

---

## 📊 CE QUE CONTIENT LE RAPPORT

Chaque vendredi, tu reçois un PDF avec:

✅ **Statistiques globales**
- Total de palettes en attente
- Temps d'attente moyen
- Nombre de palettes critiques (>28j)

✅ **Palettes par zone délai**
- 🟢 0-15 jours
- 🔵 15-21 jours
- 🟡 21-28 jours
- 🔴 +28 jours (CRITIQUE!)

✅ **Top 5 clients** (qui ont le plus de palettes)

✅ **Palettes à traiter urgemment** (>28j)

---

## 🛠️ DÉPANNAGE

### ❌ "Authentication failed"
→ Ton `SMTP_PASSWORD` est incorrect
→ Revérifie le mot de passe d'app Gmail

### ❌ "No credentials in secrets"
→ Tu n'as pas rempli tous les secrets
→ Ajoute `FIREBASE_URL`, `SMTP_USER`, `SMTP_PASSWORD`, `RAPPORT_EMAIL`

### ❌ "Firebase connection error"
→ L'URL Firebase est incorrecte
→ Vérifie que c'est l'URL du **bon rack** (retour, pas délais)

### ✅ L'action est verte mais pas de mail
→ Vérifie dans ton dossier **Spam/Indésirable**
→ Le mail a peut-être été filtré

---

## 📞 SUPPORT

Si quelque chose ne marche pas:
1. Regarde les **logs** de l'action (Actions → dernière run → generate-report)
2. Cherche les **messages d'erreur** en rouge
3. Corrige le secret correspondant

---

## 🎉 C'EST TOUT!

Ton système est prêt! Chaque vendredi à 17h:
- ✅ Le rapport se génère automatiquement
- ✅ Un PDF est créé
- ✅ Il est envoyé par mail
- ✅ Zero effort de ta part

**Profite ! 🚀**
