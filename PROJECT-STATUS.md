# Projet TVT NVR → SDK → MQTT → Home Assistant — État d'avancement

Dernière mise à jour : 2026-08-25

## Objectif actif

Architecture retenue :

```text
TVT NVR → SDK TVT Linux → MQTT → Home Assistant
```

La voie SDK est la base active du projet. L'ancien poller HTTP/API et l'ancienne intégration webhook/TCP restent historiques et ne doivent pas servir de référence fonctionnelle actuelle.

## Règles de travail du projet

### Sauvegarde avant modification importante

Avant toute modification importante touchant le LXC, le container, le SDK, les bibliothèques, le réseau, Docker ou la configuration système :

1. créer un snapshot ou un backup du LXC Proxmox concerné ;
2. noter la date, le nom du snapshot/backup et la raison dans le journal du projet ;
3. conserver aussi un backup local du fichier applicatif modifié lorsque pertinent ;
4. seulement ensuite effectuer la modification.

Aucune grosse modification ne doit être engagée sans point de retour connu.

### Travail multi-projets

Le travail peut être interrompu et repris selon le temps disponible. Chaque projet doit donc conserver en permanence :

- son état actuel ;
- les fonctions réellement validées ;
- les tests encore à faire ;
- les bugs ouverts et leur diagnostic ;
- les décisions techniques prises ;
- la prochaine étape exacte ;
- les sauvegardes/snapshots importants ;
- les éléments nécessaires pour reprendre dans un nouveau chat sans réexpliquer l'historique.

### Critère de clôture

Un projet n'est considéré comme terminé que lorsque :

- les fonctions prévues sont validées en situation réelle ;
- les bugs bloquants sont résolus ou explicitement documentés comme limites acceptées ;
- la documentation correspond à l'état réellement déployé ;
- le code/configuration final est sauvegardé dans GitHub quand applicable ;
- un backup/snapshot final ou une procédure de restauration existe ;
- les anciennes pistes, fichiers et entités obsolètes sont nettoyés ou clairement archivés ;
- le statut du projet passe explicitement à `CLÔTURÉ`.

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

## TODO complémentaire

- [ ] Étudier la gestion du **volume VLC** utilisé pour les annonces : niveau global, volume par type d'annonce, restauration du volume précédent après diffusion et comportement en cas de plusieurs annonces successives.
- [ ] Ajouter un **mode Silence / Vacances** pour les annonces audio.
- [ ] Prévoir des **horaires configurables** pour ce mode Silence / Vacances, avec règles distinctes si nécessaire selon les jours ou périodes.
- [ ] Concevoir un **système global de réveil mobile** dans Home Assistant, indépendant du seul projet NVR/annonces et réutilisable par d'autres automatisations.
- [ ] Exposer au minimum : prochain réveil connu, téléphone source, validité/fraîcheur de l'information, état `réveil_programmé`, et décalages configurables avant/après réveil.
- [ ] Prévoir une logique de repli configurable si aucune information de réveil valide n'est disponible.
- [ ] Utiliser ensuite ce système global comme source optionnelle pour le mode Silence / Vacances des annonces.
- [ ] Prévoir l'activation/désactivation de cette logique liée au réveil mobile et le choix du téléphone de référence.
- [ ] Définir le comportement des annonces prioritaires pendant le mode Silence / Vacances : blocage total, volume réduit ou exceptions pour les alertes critiques.
- [ ] Ajouter un **flow Node-RED global de surveillance des batteries** pour les équipements remontés dans Home Assistant.
- [ ] Prévoir des seuils de batterie configurables (alerte basse, critique et éventuellement seuil spécifique par équipement) ainsi que la gestion des capteurs indisponibles ou dont la valeur n'est plus mise à jour.
- [ ] Ajouter un **rappel automatique** tant qu'une batterie reste sous le seuil et qu'aucun remplacement/rechargement n'a été constaté, avec fréquence configurable et anti-spam.
- [ ] Prévoir l'acquittement temporaire d'une alerte batterie et la remise à zéro automatique du rappel dès que la batterie repasse au-dessus du seuil défini.
- [ ] Produire un résumé exploitable dans Home Assistant/Node-RED : équipements concernés, niveau de batterie, durée sous seuil et dernière notification envoyée.
- [ ] Étudier une **interface vocale mobile globale** permettant d'interroger Home Assistant avec un mot d'activation de type `Jarvis`, indépendamment du seul projet NVR.
- [ ] Évaluer le chemin complet `mot d'activation → capture vocale → reconnaissance vocale → Assist/Home Assistant → réponse → TTS sur le mobile`, avec priorité à une solution utilisable écran verrouillé si la plateforme mobile le permet.
- [ ] Prévoir que cette interface puisse servir à la fois aux **questions d'état** (`Jarvis, la porte de l'atelier est-elle fermée ?`), aux **commandes** (`éteins le garage`) et au lancement de scénarios/flows Node-RED.
- [ ] Étudier le fonctionnement local et distant, les permissions Android, la consommation batterie du wake word permanent, la confidentialité, ainsi qu'un mode de secours par bouton/raccourci si l'écoute permanente n'est pas fiable.
- [ ] Garder le mot d'activation et le moteur vocal **paramétrables**, afin de ne pas figer l'architecture sur le nom `Jarvis` ni sur un moteur STT/TTS particulier.
- [ ] Prévoir un **mode conversation par session** : un appui unique sur un bouton/raccourci mobile ouvre la conversation, puis le mobile continue d'écouter automatiquement pendant une durée ou une période d'inactivité configurable sans nouvel appui entre chaque échange.
- [ ] Prévoir une temporisation configurable de fin de session, remise à zéro après chaque interaction, avec arrêt manuel immédiat possible et indication claire lorsque l'écoute est active.
- [ ] Étudier la possibilité de prolonger automatiquement la session tant qu'un échange est en cours, puis de revenir à l'état inactif après le délai défini pour limiter la consommation batterie et les risques d'écoute permanente.

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
