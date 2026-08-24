# Journal d'avancement — TVT NVR → SDK → MQTT → Home Assistant

## 2026-08-24 — Reprise propre sur le SDK TVT

### Diagnostic de la version active

- Vérification du container Docker `tvt2mqtt`.
- Commande réellement exécutée : `python /app/app.py`.
- Constat : le `/app/app.py` actif était un poller HTTP/API, alors que la voie de travail attendue est le SDK TVT.
- Ancienne version SDK retrouvée dans `/app/app.py.bak_20260307`.
- Restauration de cette version SDK comme `/app/app.py`.

### MQTT

- Variables d'environnement contrôlées.
- Connectivité TCP vers le broker `192.168.1.20:1883` validée depuis le container.
- Publication MQTT SDK confirmée sur `tvt/nvr1/#`.

### SDK smart subscriptions

`NET_SDK_SetSubscribCallBack()` retourne `True`.

Résultats observés :

```text
SmartSubscrib FAIL cmd=20 name=vehicle_ipc err=96
SmartSubscrib FAIL cmd=21 name=intrusion_enter_ipc err=96
SmartSubscrib FAIL cmd=22 name=intrusion_leave_ipc err=96
SmartSubscrib ok cmd=25 name=pea_target
SmartSubscrib ok cmd=26 name=vsd
SmartSubscrib ok cmd=29 name=vehicle
SmartSubscrib ok cmd=30 name=intrusion_enter
SmartSubscrib ok cmd=31 name=intrusion_leave
SmartSubscrib ok cmd=38 name=line_cross
```

### Nettoyage partiel MQTT

Suppression de plusieurs retained issus de l'ancien poller HTTP/API, notamment :

```text
tvt/nvr1/aoientry/ch01
tvt/nvr1/alarm_out/out01
tvt/nvr1/alarm_out/out02
tvt/nvr1/alarm_out/out03
tvt/nvr1/alarm_out/out04
```

### Validation AOI Entry CH01

Configuration NVR contrôlée :

- `GetSmartAoiEntryConfig/1` → `switch=true`
- `GetSmartPerimeterConfig/1` → `switch=false`
- `GetSmartTripwireConfig/1` → `switch=false`
- `GetSmartAoiLeaveConfig/1` → `switch=false`

Test physique :

```text
tvt/nvr1/intrusion_enter/ch01 ON
tvt/nvr1/cmd/debug smart cmd=30 name=intrusion_enter len=442196 ch=1
tvt/nvr1/intrusion_enter/ch01 OFF
```

Conclusion : `cmd=30` est validé pour AOI Entry NVR sur CH01.

### Home Assistant

MQTT Discovery de test créé pour :

- AOI Entry CH01 ;
- Motion CH01.

AOI Entry apparaît correctement dans Home Assistant.

### Correction Motion CH01

Symptôme : Home Assistant restait en état `Détecté` après un événement motion.

Cause : le callback `ALARM_MOTION` publiait seulement `ON`.

Correction appliquée : remplacement par `pulse(topic)` afin de produire un `OFF` automatique.

Backup avant modification :

```text
/app/app.py.before_motion_fix_20260316
```

### Point de reprise

Priorité absolue : valider physiquement que `motion/ch01` produit maintenant :

```text
ON
OFF
```

Tant que ce test n'est pas validé, ne pas généraliser le Discovery ni les autres canaux.

---

## Historique précédent

Le dépôt contenait une ancienne intégration Home Assistant directe basée sur webhook/TCP brut. Cette architecture reste conservée dans l'historique du dépôt mais n'est plus la voie active du projet.
