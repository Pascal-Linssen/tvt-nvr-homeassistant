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

## Backlog priorisé

### P0 — À finir avant de disperser le projet

- [ ] Revalider physiquement le cycle `motion/ch01 ON → OFF` après correction.
- [ ] Ajouter les **flux vidéo utiles à l'interface alarme Home Assistant** afin d'avoir un accès direct aux caméras liées aux zones de sécurité.
- [ ] Définir le mapping `zone/capteur d'alarme → caméra pertinente` pour afficher immédiatement la bonne vue lors d'un événement.
- [ ] En **mode Absence**, tester l'envoi automatique d'un **snapshot de la caméra concernée** lors d'une détection pertinente, en complément de la notification d'alarme.
- [ ] Prévoir anti-spam / temporisation pour éviter une rafale de captures lors d'un même événement et vérifier le délai réel entre détection, capture et réception sur le mobile.
- [ ] Définir le comportement de repli si le snapshot échoue : conserver au minimum la notification texte et un lien/accès rapide au flux vidéo.
- [ ] Nettoyer les anciennes entités Home Assistant et les retained MQTT Discovery obsolètes.
- [ ] Stabiliser et documenter complètement le bridge `TVT NVR → SDK → MQTT → Home Assistant` avant généralisation aux autres caméras.

### P1 — Fonctions utiles à court terme

#### Annonces audio

- [ ] Étudier la gestion du **volume VLC** : niveau global, volume par type d'annonce, restauration du volume précédent après diffusion et gestion de plusieurs annonces successives.
- [ ] Ajouter un **mode Silence / Vacances**.
- [ ] Rendre les horaires de ce mode **entièrement configurables**.
- [ ] Définir le comportement des annonces prioritaires pendant le mode Silence / Vacances : blocage, volume réduit ou exception pour les alertes critiques.

#### Surveillance batteries

- [ ] Ajouter un **flow Node-RED global de surveillance des batteries** pour les équipements remontés dans Home Assistant.
- [ ] Prévoir des seuils configurables : batterie basse, critique et éventuellement seuil spécifique par équipement.
- [ ] Gérer les capteurs indisponibles ou dont la valeur ne se met plus à jour.
- [ ] Ajouter un **rappel automatique** tant qu'une batterie reste sous le seuil, avec fréquence configurable et anti-spam.
- [ ] Prévoir un acquittement temporaire et une remise à zéro automatique lorsque la batterie repasse au-dessus du seuil.
- [ ] Produire un résumé exploitable dans Home Assistant/Node-RED : équipement, niveau, durée sous seuil et dernière notification.

### P2 — Briques globales Home Assistant

#### Réveil mobile global

- [ ] Concevoir un **système global de réveil mobile** indépendant du projet NVR/annonces et réutilisable par d'autres automatisations.
- [ ] Exposer au minimum : prochain réveil connu, téléphone source, validité/fraîcheur, état `réveil_programmé` et offsets configurables avant/après réveil.
- [ ] Prévoir une logique de repli configurable si aucune information de réveil valide n'est disponible.
- [ ] Permettre le choix du téléphone de référence et l'activation/désactivation de cette logique.
- [ ] Utiliser ensuite ce système comme source optionnelle pour le mode Silence / Vacances, mais aussi pour d'autres automatisations futures.

#### Interface vocale mobile / Jarvis

- [ ] Étudier une **interface vocale mobile globale** permettant d'interroger Home Assistant avec un mot d'activation de type `Jarvis`.
- [ ] Évaluer le chemin complet `activation → capture vocale → STT → Assist/Home Assistant → réponse → TTS mobile`.
- [ ] Prévoir les questions d'état, les commandes et le lancement de scénarios/flows Node-RED.
- [ ] Étudier le fonctionnement local/distant, écran verrouillé, permissions Android, consommation batterie et confidentialité.
- [ ] Garder le mot d'activation et les moteurs STT/TTS **paramétrables**.
- [ ] Prévoir un **mode conversation par session** : un seul appui sur un bouton/raccourci ouvre la conversation, puis le mobile continue d'écouter automatiquement pendant une durée configurable.
- [ ] Prévoir une temporisation de fin de session remise à zéro après chaque interaction, avec arrêt manuel immédiat et indication claire de l'écoute active.

### P3 — Jarvis proactif / fonctions avancées

- [ ] Étudier un **mode conversation initiée par Jarvis** : Home Assistant/Node-RED peut poser spontanément une question sur le mobile, diffuser la question en TTS puis ouvrir une fenêtre d'écoute sans interaction tactile.
- [ ] Préserver le **contexte de la question** pour interpréter des réponses courtes (`oui`, `non`, `ce soir`, `dans 30 minutes`, etc.).
- [ ] Prévoir un délai de réponse configurable et une action de repli si aucune réponse n'est reçue.
- [ ] Ajouter des niveaux de priorité et respecter le mode Silence / Vacances pour éviter les sollicitations inutiles.
- [ ] Étudier une éventuelle activation par wake word permanent uniquement si le fonctionnement Android et la consommation sont jugés acceptables ; conserver le bouton/raccourci comme solution fiable de base.

## Prochaine étape prioritaire

Ordre de travail immédiat :

1. Revalider physiquement `tvt/nvr1/motion/ch01 ON → OFF`.
2. Ajouter les flux vidéo nécessaires dans l'interface alarme.
3. Associer chaque zone/capteur critique à la caméra correspondante.
4. Tester en mode **Absence** l'envoi d'une notification avec snapshot sur une détection réelle, avec anti-spam et solution de repli si la capture échoue.

Commande de test motion :

```bash
mosquitto_sub -R -h 192.168.1.20 -u tvt2mqtt -P '<secret>' -t 'tvt/nvr1/motion/ch01' -v
```

Le manuel NVR confirme que les alarmes peuvent déclencher une capture automatique via la fonction `Snapshot`; cette capacité pourra servir de référence lors du choix de la méthode de capture, même si l'intégration Home Assistant/Node-RED devra être validée séparément.

## Références

- `WORKFLOW-SDK-MQTT-REPRISE.md` : workflow complet de reprise
- `BUGS.md` : bugs ouverts / résolus
- `CHANGELOG-PROJET.md` : journal chronologique des avancées
