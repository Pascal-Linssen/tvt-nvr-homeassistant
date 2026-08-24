# Projet TVT NVR → SDK → MQTT → Home Assistant — État d'avancement

Dernière mise à jour : 2026-08-24

## Objectif actif

Architecture retenue :

```text
TVT NVR → SDK TVT Linux → MQTT → Home Assistant
```

La voie SDK est la base active du projet. L'ancien poller HTTP/API et l'ancienne intégration webhook/TCP restent historiques et ne doivent pas servir de référence fonctionnelle actuelle.

## Infrastructure

- NVR : `TD-3308H1-8P-B2-B`
- IP NVR : `192.168.1.90`
- Port SDK : `6036`
- LXC Proxmox : `200` (`tvt2mqtt`)
- IP LXC : `192.168.1.91`
- Container Docker : `tvt2mqtt`
- Image : `tvt2mqtt:latest`
- Commande container : `python /app/app.py`
- Broker MQTT : `192.168.1.20:1883`
- Préfixe MQTT : `tvt/nvr1`

Les secrets ne doivent jamais être stockés dans GitHub.

## Avancement validé

### Bridge SDK

- [x] SDK Linux chargé via `libdvrnetsdk.so`
- [x] `NET_SDK_Init()` validé
- [x] `NET_SDK_Login()` validé
- [x] `NET_SDK_SetDVRMessageCallBackEx()` validé
- [x] `NET_SDK_SetupAlarmChan()` validé
- [x] `NET_SDK_SetSubscribCallBack()` validé
- [x] `NET_SDK_SmartSubscrib()` validé pour plusieurs événements NVR
- [x] Publication MQTT fonctionnelle

### SmartSubscrib observés

| cmd | Nom actuel | Résultat |
|---:|---|---|
| 20 | `vehicle_ipc` | FAIL `err=96` |
| 21 | `intrusion_enter_ipc` | FAIL `err=96` |
| 22 | `intrusion_leave_ipc` | FAIL `err=96` |
| 25 | `pea_target` | OK |
| 26 | `vsd` | OK |
| 29 | `vehicle` | OK |
| 30 | `intrusion_enter` | OK |
| 31 | `intrusion_leave` | OK |
| 38 | `line_cross` | OK |

### AOI Entry CH01

Configuration contrôlée :

- AOI Entry = ON
- Perimeter = OFF
- Tripwire = OFF
- AOI Leave = OFF

Test réel validé :

```text
tvt/nvr1/intrusion_enter/ch01 ON
tvt/nvr1/cmd/debug smart cmd=30 name=intrusion_enter len=442196 ch=1
tvt/nvr1/intrusion_enter/ch01 OFF
```

Conclusion validée : `cmd=30` correspond à l'événement AOI Entry NVR sur CH01.

### Motion CH01

Le mouvement remonte bien via le callback alarme classique.

Bug identifié : l'ancien code publiait uniquement `ON`, sans retour automatique à `OFF`.

Correction appliquée :

```python
if alarm_type == ALARM_MOTION:
    topic = f"{TOPIC_PREFIX}/motion/ch{ch:02d}" if ch else f"{TOPIC_PREFIX}/motion/global"
    pulse(topic)
    continue
```

Backup créé avant correction :

```text
/app/app.py.before_motion_fix_20260316
```

État actuel : **patch appliqué mais test physique ON → OFF encore à revalider**.

### Home Assistant

- [x] MQTT Discovery testé avec succès pour AOI Entry CH01
- [x] Entité motion CH01 créée
- [ ] Motion CH01 à revalider après correction du retour `OFF`
- [ ] Nettoyage complet des anciennes entités / retained Discovery

## Prochaine étape prioritaire

Tester physiquement :

```text
tvt/nvr1/motion/ch01 ON
tvt/nvr1/motion/ch01 OFF
```

Commande de test :

```bash
mosquitto_sub -R -h 192.168.1.20 -u tvt2mqtt -P '<secret>' -t 'tvt/nvr1/motion/ch01' -v
```

Ne pas généraliser aux autres caméras avant validation de ce cycle.

## Références

- `WORKFLOW-SDK-MQTT-REPRISE.md` : workflow complet de reprise
- `BUGS.md` : bugs ouverts / résolus
- `CHANGELOG-PROJET.md` : journal chronologique des avancées
