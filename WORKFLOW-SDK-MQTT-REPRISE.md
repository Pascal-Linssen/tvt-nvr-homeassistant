# TVT NVR → SDK → MQTT → Home Assistant — Workflow de reprise

> État documenté après les tests de reprise du bridge SDK.
>
> **Important : la voie de travail active est le SDK TVT.** L'ancien poller HTTP/API et l'ancienne intégration Home Assistant webhook/TCP restent des pistes historiques mais ne doivent pas être considérés comme la base fonctionnelle actuelle.

## 1. Objectif

Construire un bridge fiable :

```text
TVT NVR → SDK TVT Linux → MQTT → Home Assistant
```

Fonctions prioritaires :

- mouvement par caméra ;
- entrée dans une zone AOI ;
- événements smart complémentaires (AOI Leave, Tripwire, Vehicle, PEA) si validés ;
- états exploitables dans Home Assistant via MQTT Discovery.

L'objectif immédiat est d'obtenir des événements MQTT bruts fiables avant de généraliser les entités Home Assistant.

---

## 2. Infrastructure connue

### NVR

- modèle : `TD-3308H1-8P-B2-B`
- IP : `192.168.1.90`
- port SDK / netPort : `6036`
- port HTTP : `80`
- RTSP : `554`
- firmware observé : `1.4.12.76672B250120.N0A.U1(8A418)`
- API déclarée : `2.0.0`

### Bridge

- LXC Proxmox : `200`
- nom logique : `tvt2mqtt`
- IP : `192.168.1.91`
- dossier hôte : `/opt/tvt2mqtt`
- container Docker : `tvt2mqtt`
- image : `tvt2mqtt:latest`
- commande réellement exécutée :

```text
python /app/app.py
```

### MQTT

- broker : `192.168.1.20:1883`
- compte dédié : `tvt2mqtt`
- **ne pas stocker le mot de passe MQTT ni les identifiants NVR dans GitHub** ; les fournir uniquement via variables d'environnement / gestionnaire de secrets.

Variables attendues dans le container :

```text
MQTT_HOST
MQTT_PORT
MQTT_USER
MQTT_PASS
TOPIC_PREFIX
TVT_IP
TVT_PORT
TVT_USER
TVT_PASS
```

Préfixe MQTT actuel :

```text
tvt/nvr1
```

---

## 3. SDK TVT utilisé

Archive de travail :

```text
NetSdk.cpp.linux.1.3.2.202601161500.zip
```

Bibliothèque chargée dans le container :

```text
./libs/libdvrnetsdk.so
```

Le bridge Python utilise `ctypes` pour appeler le SDK TVT.

Fonctions SDK utilisées et validées au moins au niveau initialisation / abonnement :

```text
NET_SDK_Init
NET_SDK_Login
NET_SDK_SetDVRMessageCallBackEx
NET_SDK_SetupAlarmChan
NET_SDK_SetSubscribCallBack
NET_SDK_SmartSubscrib
NET_SDK_GetLastError
```

---

## 4. Incident important : mauvaise version de app.py

Le container tournait encore, mais `/app/app.py` avait été remplacé par un poller HTTP utilisant :

```text
GetAlarmStatusInfo
urllib.request
xml.etree.ElementTree
```

Ce fichier n'était plus le bridge SDK attendu.

La bonne version SDK a été retrouvée dans :

```text
/app/app.py.bak_20260307
```

Indices confirmant qu'il s'agissait bien du bridge SDK :

```text
import ctypes
LIB_PATH = "./libs/libdvrnetsdk.so"
NET_SDK_Init
NET_SDK_Login
NET_SDK_SetSubscribCallBack
NET_SDK_SmartSubscrib
```

La version SDK a été restaurée dans :

```text
/app/app.py
```

L'ancienne version API a été sauvegardée avant remplacement.

---

## 5. Vérifications container et réseau

Le container a été confirmé actif avec :

```bash
docker ps --filter name=tvt2mqtt
```

Commande réelle :

```text
python /app/app.py
```

Le broker MQTT est joignable depuis le container sur `192.168.1.20:1883`.

Un ancien historique de logs montrait `ConnectionRefusedError`, mais le test TCP actuel a confirmé :

```text
MQTT TCP OK
```

Attention : `docker logs` contient des traces anciennes ; toujours utiliser les timestamps avant de conclure qu'une erreur est actuelle.

---

## 6. Abonnements smart SDK réellement observés

Après redémarrage du bridge SDK :

```text
SetSubscribCallBack=True
```

Résultats `NET_SDK_SmartSubscrib` :

```text
cmd=20 vehicle_ipc          FAIL err=96
cmd=21 intrusion_enter_ipc FAIL err=96
cmd=22 intrusion_leave_ipc FAIL err=96
cmd=25 pea_target          OK
cmd=26 vsd                 OK
cmd=29 vehicle             OK
cmd=30 intrusion_enter     OK
cmd=31 intrusion_leave     OK
cmd=38 line_cross          OK
```

Interprétation de travail :

- `20/21/22` correspondent à des variantes IPC non acceptées par ce NVR ;
- les variantes NVR `29/30/31` sont acceptées ;
- `38` est accepté pour Tripwire / line crossing ;
- `25` et `26` sont également acceptés.

Ne pas considérer les abonnements acceptés comme preuve qu'un événement est correctement décodé : chaque type doit encore être validé par un déclenchement réel.

---

## 7. Mapping smart validé en réel

### AOI Entry CH01

La configuration NVR de CH01 a été vérifiée :

```text
GetSmartAoiEntryConfig/1      switch=true
GetSmartPerimeterConfig/1     switch=false
GetSmartTripwireConfig/1      switch=false
GetSmartAoiLeaveConfig/1      switch=false
```

Filtres AOI Entry actifs sur CH01 :

```text
person=true
car=true
motor=true
```

Pendant une entrée réelle dans la zone AOI CH01, le bridge a publié :

```text
tvt/nvr1/intrusion_enter/ch01 ON
tvt/nvr1/cmd/debug smart cmd=30 name=intrusion_enter len=442196 ch=1
tvt/nvr1/intrusion_enter/ch01 OFF
```

### Conclusion validée

Pour ce NVR et cette configuration :

```text
cmd 30 = NVR AOI Entry / intrusion_enter
channel décodé = CH01
```

Le cycle `ON → OFF` fonctionne déjà pour cet événement grâce à la logique `pulse()` du bridge.

---

## 8. Mouvement : événement reçu mais bug ON permanent trouvé

Le SDK remonte bien des alarmes motion classiques via `NET_SDK_SetDVRMessageCallBackEx`.

Des publications ont été observées, notamment :

```text
tvt/nvr1/motion/ch01 ON
tvt/nvr1/motion/ch07 ON
```

Problème trouvé dans le code :

```python
if alarm_type == ALARM_MOTION:
    topic = f"{TOPIC_PREFIX}/motion/ch{ch:02d}" if ch else f"{TOPIC_PREFIX}/motion/global"
    payload = "ON"
```

Puis le code appelait seulement :

```python
publish(topic, payload)
```

Il n'y avait donc aucun retour automatique à `OFF` pour le mouvement.

### Correction appliquée

Le bloc motion a été modifié pour utiliser la même logique impulsionnelle que les événements smart :

```python
if alarm_type == ALARM_MOTION:
    topic = f"{TOPIC_PREFIX}/motion/ch{ch:02d}" if ch else f"{TOPIC_PREFIX}/motion/global"
    pulse(topic)
    continue
```

Backup créé avant patch :

```text
/app/app.py.before_motion_fix_20260316
```

Le container a été redémarré après modification.

### État actuel du test motion

**Le patch est présent mais le test final ON → OFF n'a pas encore été confirmé.**

Commande de reprise :

```bash
mosquitto_sub -R -h 192.168.1.20 -u tvt2mqtt -P '<secret>' \
  -t 'tvt/nvr1/motion/ch01' -v
```

Puis provoquer un mouvement réel devant CH01.

Résultat attendu :

```text
tvt/nvr1/motion/ch01 ON
tvt/nvr1/motion/ch01 OFF
```

---

## 9. MQTT brut observé

Des retained / états existants ont été observés :

```text
tvt/nvr1/alarm/armed ON
tvt/nvr1/alarm/type081 ON
tvt/nvr1/alarm/type004 ON
tvt/nvr1/alarm/type101 ON
tvt/nvr1/alarm/type068 ON
tvt/nvr1/alarm/type105 ON
tvt/nvr1/alarm/type021 ON
tvt/nvr1/motion/ch01 ON
tvt/nvr1/motion/ch07 ON
tvt/nvr1/status online
tvt/nvr1/intrusion_enter/ch01 OFF
```

Les topics `alarm/typeXXX` ne sont **pas encore décodés proprement** et ne doivent pas être transformés en entités définitives avant identification.

Des vieux topics API ont été supprimés en retained :

```text
tvt/nvr1/aoientry/ch01
tvt/nvr1/alarm_out/out01
tvt/nvr1/alarm_out/out02
tvt/nvr1/alarm_out/out03
tvt/nvr1/alarm_out/out04
```

---

## 10. Home Assistant / MQTT Discovery

Une entité de test AOI Entry a été créée via MQTT Discovery avec :

```text
state_topic = tvt/nvr1/intrusion_enter/ch01
payload_on = ON
payload_off = OFF
availability_topic = tvt/nvr1/status
payload_available = online
payload_not_available = offline
```

Elle est apparue correctement dans Home Assistant sous un nom de type :

```text
TVT NVR SDK Intrusion Enter CH01
```

Une entité Motion CH01 a également été créée et Home Assistant affichait :

```text
Détecté
```

même sans mouvement réel. La cause a été identifiée : le topic motion restait retenu à `ON` à cause du bug dans `app.py` décrit plus haut.

Le code a été corrigé, mais il reste à confirmer le comportement réel après correction.

---

## 11. Ce qui est validé aujourd'hui

### Validé

- container Docker actif ;
- bridge SDK restauré dans `/app/app.py` ;
- librairie SDK chargée ;
- accès au broker MQTT fonctionnel ;
- callback smart configuré ;
- subscriptions `25, 26, 29, 30, 31, 38` acceptées ;
- motion classique reçu au moins sur CH01 et CH07 ;
- AOI Entry CH01 réellement reçu via `cmd=30` ;
- décodage canal `ch=1` correct pour cet événement ;
- MQTT `intrusion_enter/ch01` fait bien `ON → OFF` ;
- MQTT Discovery fonctionne pour une entité test ;
- bug motion bloqué à ON identifié ;
- patch `pulse(topic)` appliqué au motion.

### Pas encore validé / problèmes restants

- test final motion CH01 `ON → OFF` après patch ;
- comportement du retained motion déjà présent dans MQTT / Home Assistant ;
- nettoyage complet des anciens topics Discovery Home Assistant ;
- suppression des anciennes entités inconnues / orphelines ;
- généralisation aux CH02–CH08 ;
- identification de `alarm/type004`, `021`, `068`, `081`, `101`, `105`, etc. ;
- décodage et validation réelle de `cmd=25`, `26`, `29`, `31`, `38` ;
- sorties d'alarme via SDK : pas encore validées dans la nouvelle reprise ;
- publication automatique MQTT Discovery depuis `app.py` : pas encore mise en place ;
- disponibilité `offline` propre lors de l'arrêt/crash du bridge : à renforcer ;
- robustesse après reboot LXC / Docker / broker : à tester ;
- core dump historique présent dans `/app/core.67`, suggérant qu'un ancien essai SDK a déjà crashé ; cause non analysée dans cette reprise.

---

## 12. Ordre de reprise recommandé

Ne pas modifier plusieurs couches à la fois.

### Étape 1 — Revalider motion CH01

```bash
mosquitto_sub -R -h 192.168.1.20 -u tvt2mqtt -P '<secret>' \
  -t 'tvt/nvr1/motion/ch01' -v
```

Déclencher un mouvement et confirmer `ON → OFF`.

### Étape 2 — Vérifier Home Assistant

Après validation MQTT brute :

- vérifier que l'entité Motion CH01 repasse réellement à `off` ;
- si elle reste `on`, inspecter le retained MQTT et l'état Discovery avant de toucher au SDK.

### Étape 3 — Nettoyer les Discovery historiques

Lister :

```bash
timeout 3 mosquitto_sub -h 192.168.1.20 -u tvt2mqtt -P '<secret>' \
  -F '%t' -t 'homeassistant/#' | grep -i 'tvt'
```

Supprimer uniquement les topics obsolètes identifiés.

### Étape 4 — Valider CH01 complètement

À obtenir avant extension :

```text
motion/ch01            ON → OFF
intrusion_enter/ch01   ON → OFF
status                 online/offline fiable
```

### Étape 5 — Étendre aux autres canaux

Seulement après validation CH01 :

```text
motion/ch02 ... ch08
intrusion_enter/ch02 ... ch08
```

### Étape 6 — Événements smart supplémentaires

Tester un à un :

```text
cmd=31 intrusion_leave
cmd=38 line_cross
cmd=29 vehicle
cmd=25 pea_target
cmd=26 vsd
```

Ne créer aucune entité HA définitive avant un test physique reproductible.

---

## 13. Commandes de diagnostic utiles

### Vérifier le container

```bash
docker ps --filter name=tvt2mqtt
```

### Vérifier la commande exécutée

```bash
docker inspect tvt2mqtt --format '{{.Config.Cmd}} {{.Config.Entrypoint}}'
```

### Vérifier le process

```bash
docker top tvt2mqtt
```

### Vérifier les variables sans afficher les secrets dans une capture publique

```bash
docker exec -it tvt2mqtt sh -c 'env | sort | grep -E "^(MQTT_HOST|MQTT_PORT|MQTT_USER|TOPIC_PREFIX|TVT_IP|TVT_PORT|TVT_USER)="'
```

### Voir les événements MQTT TVT en direct

```bash
mosquitto_sub -R -h 192.168.1.20 -u tvt2mqtt -P '<secret>' -t 'tvt/nvr1/#' -v
```

### Voir uniquement les événements smart utiles

```bash
mosquitto_sub -R -h 192.168.1.20 -u tvt2mqtt -P '<secret>' \
  -t 'tvt/nvr1/intrusion_enter/#' \
  -t 'tvt/nvr1/intrusion_leave/#' \
  -t 'tvt/nvr1/line_cross/#' \
  -t 'tvt/nvr1/pea_target/#' \
  -t 'tvt/nvr1/cmd/debug' -v
```

### Logs Docker avec timestamps

```bash
docker logs --timestamps --tail 100 tvt2mqtt
```

---

## 14. Règles à respecter pour la suite

1. **SDK = source principale active.**
2. Ne pas réintroduire le poller API comme solution principale sans raison démontrée.
3. Toujours valider MQTT brut avant Home Assistant.
4. Une commande / un test à la fois pendant le diagnostic.
5. Ne jamais stocker les mots de passe dans GitHub.
6. Ne pas généraliser un mapping smart à toutes les caméras sans test réel.
7. Garder les anciens fichiers / backups tant que la nouvelle version n'est pas stable.
8. Ne pas confondre un `SmartSubscrib OK` avec un événement réellement décodé.
9. Les anciennes entités Home Assistant webhook/TCP du dépôt sont historiques et ne représentent pas l'architecture actuellement testée.
10. Documenter immédiatement chaque mapping réellement validé.

---

## 15. Point exact de reprise

Le prochain test à effectuer est **uniquement** :

```text
Confirmer que le patch motion fait maintenant :

tvt/nvr1/motion/ch01 ON
puis
tvt/nvr1/motion/ch01 OFF
```

Tant que ce point n'est pas confirmé, ne pas étendre à d'autres caméras et ne pas reconstruire tout le MQTT Discovery.
