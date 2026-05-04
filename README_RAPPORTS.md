# 📊 AUEM RACK - Rapports Hebdomadaires Automatiques

**Système d'export automatique en PDF chaque vendredi à 17h** ✨

---

## 🎯 QU'EST-CE QUE ÇA FAIT?

Chaque **vendredi à 17h**, tu reçois automatiquement par email un **PDF complet** avec:

```
📈 Statistiques globales
├─ Total palettes en attente: 25
├─ Temps moyen d'attente: 18 jours
└─ Palettes critiques (+28j): 2

🎯 Répartition par délai
├─ 🟢 0-15 jours: 15 palettes
├─ 🔵 15-21 jours: 7 palettes
├─ 🟡 21-28 jours: 2 palettes
└─ 🔴 +28 jours (URGENT): 1 palette

🏢 Top 5 clients
1. ACME Inc - 4 palettes
2. Supplier B - 3 palettes
...

🚨 À traiter urgemment
└─ Palette B4 - ACME (30 jours!)
```

---

## ✨ AVANTAGES

✅ **Automatique** - Zero effort après le setup  
✅ **Personnalisable** - Change l'email en 2 clics  
✅ **Gratuit** - GitHub Actions gratuit, Gmail gratuit  
✅ **Fiable** - Tourne même si l'ordi est éteint  
✅ **Historique** - Tous les rapports sont gardés  
✅ **Pas de spam** - Email professionnel configuré

---

## 🚀 DÉMARRAGE RAPIDE (10 min)

### 1️⃣ Créer un repo GitHub

```
Nom: auem-rack-reports
Public: Oui
```

### 2️⃣ Uploader les fichiers

```
script_rapport.py          ← À la racine
.github/workflows/export.yml   ← Dans un dossier
requirements.txt           ← À la racine
```

### 3️⃣ Générer un App Password Gmail

1. Va sur [myaccount.google.com](https://myaccount.google.com)
2. Security → 2-Step Verification (si pas fait)
3. Security → App passwords
4. Génère pour Gmail
5. **Copie le mot de passe**

### 4️⃣ Ajouter les Secrets GitHub

Dans Settings → Secrets and variables → Actions:

| Secret | Valeur |
|--------|--------|
| `FIREBASE_URL` | `https://auem-rac-default-rtdb.europe-west1.firebasedatabase.app/retour.json` |
| `SMTP_USER` | `thuillier.kevin10@gmail.com` |
| `SMTP_PASSWORD` | `[Le mot de passe d'app Gmail]` |
| `RAPPORT_EMAIL` | `axefoxe8592@gmail.com` |

### 5️⃣ Tester

Actions → Rapport Hebdomadaire Rack → Run workflow → Attendre 2 min

✅ Tu reçois un email avec le PDF!

---

## 📝 MODIFIER LE DESTINATAIRE

**Sans toucher au code**, change l'email en 2 clics:

1. Settings → Secrets → `RAPPORT_EMAIL` → ✏️
2. Change l'email → Update
3. Done! ✅

---

## ⏰ QUAND EST-CE QUE ÇA S'ENVOIE?

**Chaque vendredi à 17h UTC** (équivalent à 16h en France hiver, 15h en été)

Si tu veux changer l'heure, édite la ligne dans `.github/workflows/export.yml`:
```yaml
- cron: '0 17 * * 5'  # Change le 17 par l'heure que tu veux
```

---

## 🛠️ STRUCTURE DES FICHIERS

```
auem-rack-reports/
├─ script_rapport.py          # Génère le PDF et l'envoie
├─ requirements.txt           # Dépendances Python
├─ .github/
│  └─ workflows/
│     └─ export.yml           # Planification GitHub Actions
└─ README.md                  # Ce fichier
```

---

## 🔧 VARIABLES MODIFIABLES

### RAPIDES (2 clics dans GitHub)

- **RAPPORT_EMAIL** - Qui reçoit le PDF
- **SMTP_PASSWORD** - Mot de passe Gmail

### AVANCÉES (éditer le fichier)

- **Heure d'envoi** - Dans `export.yml` (ligne cron)
- **Jour d'envoi** - Dans `export.yml` (5 = vendredi)
- **Contenu du rapport** - Dans `script_rapport.py`

---

## 📊 CONTENU DU PDF

### Toujours inclus:

✅ Titre avec semaine et année  
✅ Total de palettes  
✅ Temps moyen d'attente  
✅ Répartition par zone (0-15j, 15-21j, 21-28j, +28j)  
✅ Top 5 des clients  

### Si applicable:

🚨 **Palettes critiques** - Si y'a des trucs >28j  
⚠️ **Alertes** - Rappels importants  

---

## 🆘 DÉPANNAGE

### ❌ Erreur "Authentication failed"

**Cause**: Mot de passe Gmail incorrect

**Solution**:
1. Va sur [myaccount.google.com](https://myaccount.google.com) → App passwords
2. Génère un **nouveau** mot de passe
3. Mets à jour le secret `SMTP_PASSWORD`

### ❌ Pas d'email reçu

**Vérifications**:
1. ✅ L'action GitHub est verte (Settings → Actions)
2. ✅ Regarde dans **Spam/Indésirable**
3. ✅ Revérifie l'email dans `RAPPORT_EMAIL`

### ❌ Erreur "Firebase connection error"

**Cause**: URL Firebase incorrecte

**Solution**: Copie cette URL exactement:
```
https://auem-rac-default-rtdb.europe-west1.firebasedatabase.app/retour.json
```

### ❌ Action rouge avec erreur

1. Va dans Actions
2. Clique sur la run en rouge
3. Clique "generate-report"
4. Scroll et lis le message d'erreur
5. Corrige le secret correspondant

---

## 📧 FORMAT DE L'EMAIL

L'email est **configuré pour ne pas aller en spam** avec:

✅ Headers professionnels (From, Message-ID, etc)  
✅ Sujet clair et cohérent  
✅ HTML bien formaté  
✅ Signature AUEM Rack System  

---

## 🎓 CONCEPTS CLÉS

### GitHub Actions
Service d'automatisation gratuit de GitHub. Lance des scripts selon un planning.

### App Password
Mot de passe unique pour une app (pas ton vrai mot de passe). Plus sûr!

### Secrets
Variables cachées que GitHub ne montre pas publiquement.

### Cron
Syntaxe pour planifier les tâches (`0 17 * * 5` = 17h le vendredi)

---

## 💡 IDÉES D'EXTENSION

- 📧 Envoyer à plusieurs emails
- 📊 Ajouter des graphiques au PDF
- 🔔 Envoyer à Discord/Slack aussi
- 📱 Export en Excel aussi
- ⏰ Rapports quotidiens/mensuels

---

## 🎉 C'EST TOUT!

Ton système est **100% automatisé**. Chaque vendredi, tu reçois ton rapport sans rien faire!

**Besoin d'aide?** → Demande-moi! 👍

---

**Dernière mise à jour**: 2026-05-04  
**Version**: 1.0  
**Statut**: ✅ Production-ready
