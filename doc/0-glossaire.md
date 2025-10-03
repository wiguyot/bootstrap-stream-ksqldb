# glossaire


## Stateless (sans état)

Un traitement stateless est une opération qui traite chaque message indépendamment des autres. Cela signifie que :

- **Aucune information sur les messages passés** n’est conservée entre les appels de traitement.
- Le **résultat dépend uniquement du message courant**, sans référence à un contexte ou à un historique.
- Le **traitement est déterministe** : le même message produit toujours le même résultat, indépendamment du moment où il est traité ou des messages précédents.
- Le système n’a **pas besoin de mémoire** locale ni de stockage externe pour effectuer l’opération.

**Conséquences techniques**  :

- **Facilement scalable** (on peut paralléliser sans coordination).
- **Pas de besoin de synchronisation ou de réplication de l’état.**
- **Résilience élevée** : une instance peut tomber et reprendre le traitement ailleurs sans perte de contexte.


## Stateful (avec état)

Un traitement stateful est une opération qui **dépend d’un contexte accumulé ou partagé**, c’est-à-dire :

- Le traitement nécessite de mémoriser des données sur les messages précédemment vus (par exemple : des agrégats, des jointures, des fenêtres temporelles).
- Le résultat dépend à la fois du message courant et de l’état courant, qui évolue au fil du temps.
- Le traitement implique donc une modification de l’état interne, stocké localement (souvent dans RocksDB pour Kafka Streams) et synchronisé via un changelog sur Kafka pour la tolérance aux pannes.

**Conséquences techniques** :

- **Moins triviale à scaler** : nécessite une répartition cohérente des clés pour garantir que le bon sous-ensemble de l’état soit disponible localement.
- **Doit assurer la durabilité et la réplication de l’état pour la tolérance aux pannes.**
- **Le redémarrage d'une instance nécessite de rejouer le changelog Kafka pour restaurer l’état local.**