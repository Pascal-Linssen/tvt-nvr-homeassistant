# Bugs — TVT NVR → SDK → MQTT → Home Assistant

Dernière mise à jour : 2026-08-24

## Bugs ouverts

### BUG-001 — Motion CH01 peut rester bloqué à ON

**Statut :** correction appliquée, validation terrain en attente.

**Symptôme :** Home Assistant affichait `Détecté` alors qu'il n'y avait plus de mouvement.

**Cause identifiée :** le callback alarme classique publiait `ON` via `publish()` mais aucun `OFF` n'était généré.

**Correction :** utilisation de `pulse(topic)` pour `ALARM_MOTION`, avec retour automatique à `OFF` après `AUTO_OFF_SECONDS`.

**À faire :** valider physiquement le cycle MQTT `ON → OFF` sur CH01.

---

### BUG-002 — Anciennes entités Home Assistant en état Inconnu

**Statut :** ouvert.

**Symptôme :** anciennes entités MQTT Discovery restent présentes et/ou en état `Inconnu`.

**Cause probable :** anciens retained Discovery issus de plusieurs essais précédents et topics d'état ne correspondant plus au bridge SDK actif.

**À faire :**

1. inventorier tous les retained `homeassistant/#` contenant `tvt` ;
2. supprimer uniquement les anciens topics obsolètes ;
3. recharger MQTT dans Home Assistant ;
4. supprimer manuellement les entités orphelines restantes si nécessaire.

---

### BUG-003 — SmartSubscrib IPC échoue avec err=96

**Statut :** non bloquant / à documenter.

Échecs observés :

```text
cmd=20 vehicle_ipc          err=96
cmd=21 intrusion_enter_ipc err=96
cmd=22 intrusion_leave_ipc err=96
```

Les variantes NVR correspondantes sont acceptées (`29`, `30`, `31`).

**Décision actuelle :** ne pas bloquer le projet sur les variantes IPC ; privilégier les événements NVR validés sur ce matériel.

---

### BUG-004 — Alarm types classiques non identifiés

**Statut :** ouvert.

Topics observés :

```text
tvt/nvr1/alarm/type004
tvt/nvr1/alarm/type021
tvt/nvr1/alarm/type068
tvt/nvr1/alarm/type081
tvt/nvr1/alarm/type101
tvt/nvr1/alarm/type105
```

**À faire :** corréler chaque code avec une action réelle côté NVR et/ou les structures/énumérations SDK avant de leur donner un nom métier.

---

### BUG-005 — Sorties d'alarme non encore remontées proprement via SDK

**Statut :** ouvert.

La voie API avait permis d'observer `sensorAlarmOut`, mais la voie active du projet est désormais le SDK.

**À faire :** identifier dans le SDK le callback, type d'alarme ou fonction permettant de remonter l'état réel des sorties relais, sans revenir au poller HTTP comme source principale.

---

### BUG-006 — Ancien core dump SDK présent

**Statut :** à analyser si un nouveau crash survient.

Fichier observé :

```text
/app/core.67
```

Cela indique qu'une ancienne exécution a probablement subi un crash natif. Aucun crash actuel n'a été démontré pendant la dernière reprise.

**Décision :** ne pas perdre de temps dessus tant que le bridge actuel reste stable ; analyser immédiatement si un nouveau crash SDK se reproduit.

## Bugs résolus / contournés

### RESOLVED-001 — Mauvaise version app.py active

Le container exécutait une version HTTP/API au lieu de la version SDK recherchée.

**Solution :** restauration de `/app/app.py.bak_20260307` vers `/app/app.py`.

### RESOLVED-002 — Confusion fichier hôte / fichier container

Le fichier `/opt/tvt2mqtt/app.py` sur le LXC et `/app/app.py` dans Docker ne doivent pas être confondus.

**Règle :** toujours vérifier le fichier réellement exécuté dans le container avant toute modification ou conclusion.

### RESOLVED-003 — AOI Entry CH01 non identifié

Test terrain :

```text
tvt/nvr1/intrusion_enter/ch01 ON
smart cmd=30 name=intrusion_enter ... ch=1
tvt/nvr1/intrusion_enter/ch01 OFF
```

Avec AOI Entry activé et Perimeter / Tripwire / AOI Leave désactivés sur CH01, `cmd=30` est validé comme AOI Entry NVR pour cette installation.
