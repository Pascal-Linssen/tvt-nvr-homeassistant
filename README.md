# 📖 IntégrFonctionnalités :  
- **🔔 Contrôle d'alarme** - Panneau de contrôle d'alarme intégré
- **🔌 Commande des sorties** - Pilotage des relais et sorties du NVR
## 9. Dépannage
1. **Alarm Server** : Vérifiez que l'Alarm Server est activé et que l'IP/port sont corrects.  
2. **Connexion NVR** : Testez l'URL du NVR dans un navigateur avec vos identifiants.  
3. **Capteurs bloqués** : Vérifiez la durée des alarmes si les capteurs restent en ON.  
4. **Sorties non fonctionnelles** : Vérifiez la configuration des relais dans le NVR.
5. **Entrées non détectées** : Contrôlez le câblage et la configuration des entrées.
6. **Problèmes d'alarme** : Vérifiez le code d'accès et les permissions utilisateur.

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
