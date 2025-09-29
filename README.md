# 📖 Intégration Home Assistant – TVT NVR  

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)  
[![GitHub Release](https://img.shields.io/github/v/release/toncompte/tvt_nvr)](https://github.com/toncompte/tvt_nvr/releases)  
[![GitHub License](https://img.shields.io/github/license/toncompte/tvt_nvr)](https://github.com/toncompte/tvt_nvr/blob/main/LICENSE)  

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
Pour chaque caméra :  
- `binary_sensor.tvt_camX_motion` → Mouvement  
- `binary_sensor.tvt_camX_intrusion` → Intrusion  

---

## 6. Services disponibles
### Service : `tvt_nvr.pulse_output`  
Déclenche une impulsion sur une sortie relais.  

**Exemple :**
```yaml
service: tvt_nvr.pulse_output
data:
  output: 1
  hold: 1
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
  - type: entities
    title: 📺 État des caméras TVT
    entities:
      - entity: binary_sensor.tvt_cam1_motion
      - entity: binary_sensor.tvt_cam1_intrusion

  - type: button
    name: 🚪 Ouvrir Porte Garage
    service: tvt_nvr.pulse_output
```

---

## 9. Dépannage
1. Vérifiez que l’**Alarm Server** est activé et que l’IP/port sont corrects.  
2. Testez l’URL du NVR dans un navigateur avec vos identifiants.  
3. Vérifiez la durée des alarmes si les capteurs restent bloqués en ON.  

---
