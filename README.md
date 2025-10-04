# 📖 IntégrFonctionnalités :  
- **🔔 Contrôle d'alarme** - Panneau de contrô## 3. Installation
1. **Téléchargez l'intégr## 4. Configuration du NVR

### 🔧 **Option 1: Webhook standard (recommandé)**
Activez le **serveur d'alarme (Alarm Server)** dans :  
```
Settings → AI/Event → General Event Management → Alarm Event Notification
```

Paramètres à configurer :  
- **Adresse IP** : celle de Home Assistant  
- **Port** : 8123  
- **Chemin** : `/api/webhook/tvt_nvr_alarm_[ID]` (affiché dans Home Assistant)

### 🛠️ **Option 2: Serveur TCP brut (pour requêtes malformées)**
Si vous rencontrez des erreurs `BadHttpMessage` répétées dans les logs, utilisez cette option :

**Dans le NVR :**
- **Adresse IP** : celle de Home Assistant  
- **Port** : **8124** (au lieu de 8123)
- **Chemin** : `/` ou laissez vide

**Avantages :** 
- ✅ Élimine les erreurs `aiohttp.http_exceptions.BadHttpMessage`
- ✅ Traite les données XML malformées du NVR
- ✅ Plus stable pour les NVR TVT anciens

**Configuration du pare-feu :**
Ouvrez le port 8124 sur votre serveur Home Assistant si nécessaire.puis GitHub ou HACS
2. Dézippez le contenu dans :  
   ```
   config/custom_components/tvt_nvr/
   ```
3. **Redémarrez Home Assistant complètement** (pas seulement recharger)
4. **Videz le cache du navigateur** (Ctrl+F5 ou Cmd+Shift+R)
5. Ajoutez l'intégration via :  
   **Paramètres → Appareils & services → Ajouter une intégration → TVT NVR**

> 💡 **Note :** L'icône TVT peut prendre quelques minutes à apparaître après l'installation. Redémarrez Home Assistant si l'icône ne s'affiche pas.rme intégré
- **🔌 Commande des sorties** - Pilotage des relais et sorties du NVR
## 9. Dépannage

### 🔧 Problèmes courants

1. **Alarm Server** : Vérifiez que l'Alarm Server est activé et que l'IP/port sont corrects.  
2. **Connexion NVR** : Testez l'URL du NVR dans un navigateur avec vos identifiants.  
3. **Capteurs bloqués** : Vérifiez la durée des alarmes si les capteurs restent en ON.  
4. **Sorties non fonctionnelles** : Vérifiez la configuration des relais dans le NVR.
5. **Entrées non détectées** : Contrôlez le câblage et la configuration des entrées.
6. **Problèmes d'alarme** : Vérifiez le code d'accès et les permissions utilisateur.

### ⚠️ Erreurs HTTP communes

**Erreur "BadHttpMessage" dans les logs :**
```
aiohttp.http_exceptions.BadHttpMessage: 400, message: Data after `Connection: close`
```

**Cause :** Le NVR TVT envoie des données XML non conformes aux standards HTTP.

**Solutions :**

1. **Serveur TCP brut (Recommandé)** - Configurez le NVR pour utiliser le port **8124** au lieu de 8123. L'intégration démarre automatiquement un serveur TCP qui gère ces requêtes malformées.

2. **Logs seulement** - Gardez le port 8123 et ajoutez cette configuration pour masquer les erreurs dans les logs :
```yaml
logger:
  default: warning
  logs:
    aiohttp.server: error
    custom_components.tvt_nvr: debug
```

**Port 8124 vs 8123 :**
- **Port 8123** : Webhook standard Home Assistant (peut générer des erreurs BadHttpMessage)
- **Port 8124** : Serveur TCP brut qui gère les données malformées proprement

### 📋 Configuration NVR recommandée

**Pour éviter les erreurs BadHttpMessage :**
1. **Port recommandé** : Utilisez le port **8124** pour éviter les erreurs HTTP
2. **URL alternative** : `http://[IP_HOME_ASSISTANT]:8124/` 
3. **Intervalle d'envoi** : 30 secondes minimum pour éviter le spam
4. **Format de données** : L'intégration accepte XML et JSON sur les deux ports

**Comparaison des ports :**
| Port | Type | Avantages | Inconvénients |
|------|------|-----------|---------------|
| 8123 | Webhook HA | Standard, intégré | Erreurs BadHttpMessage |
| 8124 | TCP brut | Pas d'erreurs, stable | Port supplémentaire |

### �️ Problème d'affichage de l'icône

**L'icône TVT ne s'affiche pas :**

1. **Redémarrage complet** : Redémarrez Home Assistant complètement (pas juste recharger)
2. **Cache navigateur** : Videz le cache de votre navigateur (Ctrl+F5)
3. **Vérifiez le fichier** : Assurez-vous que `icon.jpg` existe dans `/config/custom_components/tvt_nvr/`
4. **Format d'image** : Home Assistant préfère les fichiers PNG 256x256 pixels
5. **Permissions** : Vérifiez que Home Assistant peut lire le fichier icône

**Pour convertir l'icône en PNG (optionnel) :**
```bash
# Sur Linux/macOS avec ImageMagick
convert icon.jpg -resize 256x256 icon.png

# Ou utilisez un convertisseur en ligne
```

**Fichiers requis pour l'icône :**
- `icon.jpg` (fourni) ou `icon.png` (recommandé)
- Taille recommandée : 256x256 pixels
- Format : PNG transparent ou JPG

### 📋 Log de débogage
Activez les logs détaillés en ajoutant dans `configuration.yaml` :
```yaml
logger:
  default: warning
  logs:
    custom_components.tvt_nvr: debug
```📥 Lecture des entrées** - Surveillance des entrées numériques
- **📡 Réception des événements** - Événements d'alarme en temps réel
- **📊 Capteurs binaires** - Détection mouvement, intrusion, etc.
- **🎯 Services avancés** - Contrôle complet via services Home Assistantn Home Assistant – TVT NVR  

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)  
[![GitHub Release](https://img.shields.io/github/v/release/Pascal-Linssen/tvt-nvr-homeassistant)](https://github.com/Pascal-Linssen/tvt-nvr-homeassistant/releases)  
[![GitHub License](https://img.shields.io/github/license/Pascal-Linssen/tvt-nvr-homeassistant)](https://github.com/Pascal-Linssen/tvt-nvr-homeassistant/blob/main/LICENSE)  

---

## 1. Présentation
L’intégration **`tvt_nvr`** permet de connecter un **NVR TVT (série NV9000 et compatibles)** à Home Assistant.  

Fonctionnalités :  
- Réception des événements d’alarme  
- Création automatique de capteurs binaires  
- Pilotage des sorties relais (ex. porte de garage, sirène)

---

## 2. Prérequis
- Un NVR TVT configuré sur le réseau local  
- Accès au répertoire `config/` de Home Assistant  
- Identifiants administrateur du NVR  
- **Home Assistant 2023.8 ou plus récent**

---

## 3. Installation
1. Dézippez le fichier **`tvt_nvr_integration.zip`** dans :  
   ```
   config/custom_components/tvt_nvr/
   ```
2. Redémarrez Home Assistant  
3. Ajoutez l’intégration via :  
   **Paramètres → Appareils & services → Ajouter une intégration → TVT NVR**

---

## 4. Configuration du NVR
Activez le **serveur d’alarme (Alarm Server)** dans :  
```
Settings → AI/Event → General Event Management → Alarm Event Notification
```

Paramètres à configurer :  
- **Adresse IP** : celle de Home Assistant  
- **Port** : 8123  
- **Chemin** : `/api/webhook/tvt_nvr_alarm`

---

## 5. Entités créées

### 🔔 Panneau de contrôle d'alarme
- `alarm_control_panel.tvt_nvr_alarm` → Contrôle central d'alarme

### 📊 Capteurs binaires
Pour chaque caméra :  
- `binary_sensor.tvt_camX_motion` → Détection de mouvement  
- `binary_sensor.tvt_camX_intrusion` → Détection d'intrusion
- `binary_sensor.tvt_camX_tampering` → Détection de sabotage

### 🔌 Commutateurs (Sorties)
Pour chaque sortie configurée :
- `switch.tvt_output_X` → Contrôle des relais/sorties

### 📥 Capteurs d'entrées
Pour chaque entrée configurée :
- `binary_sensor.tvt_input_X` → État des entrées numériques  

---

## 6. Services disponibles

### 🔔 Service : `alarm_control_panel.alarm_arm_away`
Arme l'alarme en mode absent.
```yaml
service: alarm_control_panel.alarm_arm_away
target:
  entity_id: alarm_control_panel.tvt_nvr_alarm
```

### 🔔 Service : `alarm_control_panel.alarm_disarm`
Désarme l'alarme.
```yaml
service: alarm_control_panel.alarm_disarm
target:
  entity_id: alarm_control_panel.tvt_nvr_alarm
data:
  code: "1234"  # Code si requis
```

### 🔌 Service : `tvt_nvr.pulse_output`  
Déclenche une impulsion sur une sortie relais.  
```yaml
service: tvt_nvr.pulse_output
data:
  output: 1
  hold: 1
```

### 🔌 Service : `switch.turn_on/turn_off`
Contrôle des sorties via les entités switch.
```yaml
service: switch.turn_on
target:
  entity_id: switch.tvt_output_1
```

---

## 7. Événements Home Assistant
Chaque alarme génère un événement interne `tvt_nvr_event`.  

**Exemple :**
```yaml
event_type: tvt_nvr_event
data:
  channel: 2
  event: motion
  on: true
```

---

## 8. Exemple Lovelace
Ajoutez ceci dans votre dashboard :

```yaml
type: vertical-stack
cards:
  # Panneau de contrôle d'alarme
  - type: alarm-panel
    entity: alarm_control_panel.tvt_nvr_alarm
    name: 🔔 Alarme TVT NVR

  # État des caméras
  - type: entities
    title: 📺 État des caméras TVT
    entities:
      - entity: binary_sensor.tvt_cam1_motion
      - entity: binary_sensor.tvt_cam1_intrusion
      - entity: binary_sensor.tvt_cam1_tampering

  # Contrôle des sorties
  - type: entities
    title: 🔌 Sorties NVR
    entities:
      - entity: switch.tvt_output_1
        name: 🚪 Porte Garage
      - entity: switch.tvt_output_2
        name: 🚨 Sirène

  # État des entrées
  - type: entities
    title: 📥 Entrées NVR
    entities:
      - entity: binary_sensor.tvt_input_1
        name: 🚪 Capteur Porte
      - entity: binary_sensor.tvt_input_2
        name: 🌡️ Capteur PIR
```

---

## 9. Dépannage
1. Vérifiez que l’**Alarm Server** est activé et que l’IP/port sont corrects.  
2. Testez l’URL du NVR dans un navigateur avec vos identifiants.  
3. Vérifiez la durée des alarmes si les capteurs restent bloqués en ON.  

---
