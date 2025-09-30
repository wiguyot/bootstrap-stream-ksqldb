


Crée le topic `temperatures` (4 partitions par exemple) :

```bash
# Avec kafka-topics (dans un conteneur Kafka si nécessaire)
docker exec -i kafka-1 \
  kafka-topics --bootstrap-server "$BROKER" \
  --create --topic temperatures --partitions 4 --replication-factor 1 --if-not-exists
```

- Ecris la commande qui va bien pour vérifier le bon fonctionnement de la commande précédente.

```bash
docker exec -i kafka-1 \
  kafka-topics --bootstrap-server "$BROKER" \
  --describe --topic temperatures
```

```yaml
Topic: temperatures     TopicId: pPr4RK6bQs-3XBcmFOeMGg PartitionCount: 4       ReplicationFactor: 1    Configs: 
        Topic: temperatures     Partition: 0    Leader: 2       Replicas: 2     Isr: 2  Offline: 
        Topic: temperatures     Partition: 1    Leader: 3       Replicas: 3     Isr: 3  Offline: 
        Topic: temperatures     Partition: 2    Leader: 1       Replicas: 1     Isr: 1  Offline: 
        Topic: temperatures     Partition: 3    Leader: 1       Replicas: 1     Isr: 1  Offline: 
```

- l'URL sur le control center est : "http://localhost:9021"
  
On va dans **topics** puis à nouveau sur **topics** et on choisi le topic **temperatures** puis **messages**.

Par défaut on a les messages arrivés dans l'ordre qui arrange "la machine". 

On peut voir les partions en sautant à "l'offset 0" et là un selecteur apparait pour choisir l'offset 0 de quelle partition. 

Au travers de l'exament des partitions on s'apperçoit que la partition 2 n'a pas de messages. En fait le hachage Murmur2 avec les villes choisies ne fait rien tomber dans la partition 2. Plus tard on verra que si on utilise la ville Montpellier on arrive à utiliser la partition 2.

- tous les enregistrement de S_TEMP_RAW qui ont comme ville Paris

```sql
-- (facultatif) lire depuis le début au lieu des seuls nouveaux messages
SET 'auto.offset.reset'='earliest';

-- filtre exact (sensible à la casse)
SELECT * FROM S_TEMPS_RAW
WHERE ville = 'Paris'
EMIT CHANGES;
```

Si on met pas auto.offset.reset à **earliest** on a que les nouveaux enregistrements.
Le EMIT CHANGES permet de laisser le flux ouvert et de rajouter les nouveaux messages satisfaisant la condition.

Donc à la question "Si vous lancez l'émission de nouveaux messages dans ce topic et que vous relanciez en même temps l'affichage de ```sql select * from S_TEMPS_RAW; ```" on a que les nouveaux enregistrement. Il faut rajouter ```sql SET 'auto.offset.reset'='earliest';``` pour avoir les anciens messages et les nouveaux satisfaisant la condition.


- Au moyen des requêtes suivantes vérifie la clé utilisée :

```sql
SHOW STREAMS;
DESCRIBE  S_TEMPS_BY_VILLE;
```

le champ suivant porte la mention key : 

```json
    "fields": [
      {
        "name": "VILLE",
        "schema": {
          "type": "STRING",
          "fields": null,
          "memberSchema": null
        },
        "type": "KEY"
```


- Dans l'onglet ksqlDB du Control Center à quoi correpond "Persistent queries" et expliquez pourquoi c'est une requête persistante.
  
  En fait c'est le code ksqlDB qui permet d'alimenter le topic "temperatures_by_villes" qui tient sa source du STREAM S_TEMPS_RAW avec comme clé de partition S_TEMPS_RAW.VILLE


- la requête :

```sql 
CREATE TABLE T_MAX_5M AS
SELECT
  ville,
  WINDOWSTART AS w_start,
  WINDOWEND   AS w_end,
  MAX(t)      AS t_max
FROM S_TEMPS_BY_VILLE
WINDOW TUMBLING (SIZE 5 MINUTES, GRACE PERIOD 30 SECONDS)
GROUP BY ville
EMIT CHANGES;
```

On voit dans ksqldb / persistent queries la mise à jour des requêtes persistantes : 
    - CSAS_S_TEMPS_BY_VILLE_1 qui a été créé un peu plus haut.
    - CTAS_T_MAX_5M_3 qui génère nos températures maximums par ville sur une fenêtre non chevauchantes de 5 minutes avec un délai de retard maximum de 30 secondes pour que la donnée soit prise en compte.
    - EMIT CHANGES génère la mise à jour des agrégats au fil de l'eau.

- Dans l'onglet ksqldb lancez la requête suivante pendant que vous injectez de nouveaux messages dans le topic **temperatures** : 

```sql
-- Affiche en continu les fenêtres qui se remplissent
SELECT * FROM T_MAX_5M EMIT CHANGES;
```

Expliquez ce que vous voyez. Pensez à faire un tri sur la colonne ville pour que cela devienne plus clair.

En fait dès qu'une valeur de température dépasse la précédente enregistrée pour la ville en question sur la fenêtre de temps alors le message est enregistré. Donc le dernier message enregistré pour chaque ville représente le max de tempérarure sur les 5 dernières minutes.

Quand on sort de la fenêtre de temps il ne reste que la dernière valeur max par ville d'enregistrée.



- Les dernières valeurs par ville 

Table non fenêtrée avec la dernière température observée par ville :

```sql
CREATE TABLE T_LAST AS
SELECT ville,
       LATEST_BY_OFFSET(t) AS t_last,
       LATEST_BY_OFFSET(ts) AS ts_last
FROM S_TEMPS_BY_VILLE
GROUP BY ville
EMIT CHANGES;
```

Pour vérifier le bon fonctionner on peut par exemple aller sur l'affichage en continue de la table T_LAST (control center / ksqlDB / ksql / tables / query table )


- une requête pour avoir la dernière température de la ville de Lyon : 


```sql
SELECT t_last, ts_last, ville FROM T_LAST WHERE ville='Lyon';
```


- HOPPING Fenêtre glissante de 10 min, **saut** de 2 min :

```sql
CREATE TABLE T_AVG_10M_HOP2 AS
SELECT
  ville,
  WINDOWSTART AS w_start,
  WINDOWEND   AS w_end,
  AVG(t)      AS t_avg
FROM S_TEMPS_BY_VILLE
WINDOW HOPPING (SIZE 10 MINUTES, ADVANCE BY 2 MINUTES)
GROUP BY ville
EMIT CHANGES;
```

Mettez en oeuvre le HOPPING tel que décrit ci-dessus. Montrez l'évolution de la table correspondante.
=> on attend des requêtes comme les précédentes mais sur la table **T_AVG_10M_HOP2**.

