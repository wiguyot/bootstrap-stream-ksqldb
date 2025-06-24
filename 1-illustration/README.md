# Mise en oeuvre ksqldb

## Objectifs pédagogiques

- réaliser un producteur Python qui écrit dans un topic "commandes" des informations ville, montant des commandes, timestamp le tout dans un format JSON
- Créer un STREAM ksqldb qui va lire ce topic en continue.
- Visualiser les résultats en direct dans un terminal au moyen d'un SELECT sur le STREAM précédement créé. L'astuce par rapport au SQL classique est de rajouter ```EMIT CHANGES``` afin que la visualisation du STREAM s'actualise.
  
## définition STREAM

Un STREAM dans ksqlDB est une vue en lecture seule et en temps réel d’un topic Kafka, qui représente une séquence continue d’événements (row-based), traitée comme une table en lecture seule qui évolue dans le temps.

## Production de l'infra docker

Dans le répertoire courant (1-illustration) on va pouvoir trouver
- le docker-compose.yml à lancer => docker compose up --build

On pourra lancer un terminal sur le container ksqldb pour exécuter la commande ksql qui a besoin de l'URL de connexion au serveur. Dans ce cas on pourr mettre soit
- http://ksqldb:8088
- http://localhost:8088 car on se trouve déjà sur ksqldb

```bash
docker compose run ksqldb ksql http://ksqldb:8088
```

puis exécuter les requêtes : 

Visualiser les topics : 

```sql
show topics;
```

Créer le stream stream_commandes : 

```sql
CREATE STREAM stream_commandes (
  ville VARCHAR,
  montant DOUBLE,
  ts BIGINT
) WITH (
  KAFKA_TOPIC='commandes',
  VALUE_FORMAT='JSON',
  TIMESTAMP='ts'
);
```

- Crée un STREAM nommé stream_commandes ayant comme champs : 
  - ville
  - montant
- correspondant :
  - au TOPIC : 'commandes'
  - utilisant JSON comme format des valeurs
  - le timestamp est dans le champ 'ts'

On peut voir les STREAMS créés : 

```sql
show streams;
```

Pour un résultat qui serait : 
```sql
ksql> show streams;

 Stream Name      | Kafka Topic | Key Format | Value Format | Windowed 
-----------------------------------------------------------------------
 STREAM_COMMANDES | commandes   | KAFKA      | JSON         | false    
-----------------------------------------------------------------------
```

Une requête d'affichage du contenu de ce stream stream_commandes : 
```sql 
SELECT ville, COUNT(*) 
FROM stream_commandes
WINDOW TUMBLING (SIZE 1 MINUTE)
GROUP BY ville
EMIT CHANGES;
``` 

Sans interompre cette requête sur le STREAM stream_commandes on peut ouvrir un nouveau client ksql dans un autre terminal : 
```bash
docker compose run ksqldb ksql http://ksqldb:8088
```

Et avec la commande suivante on va pouvoir voir les requêtes actives : 
```sql
show queries;
```

Le resultat serait quelque chose comme : 
```
 Query ID                                       | Query Type | Status    | Sink Name | Sink Kafka Topic | Query String                                                                                               
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 transient_STREAM_COMMANDES_7603518550648374577 | PUSH       | RUNNING:1 |           |                  | SELECT ville, COUNT(*)  FROM stream_commandes WINDOW TUMBLING (SIZE 1 MINUTE) GROUP BY ville EMIT CHANGES; 
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
```

Si on interrompt par un ```Ctrl+C``` la visualisation de la requête alors :
```sql
ksql> show queries;

 Query ID | Query Type | Status | Sink Name | Sink Kafka Topic | Query String 
------------------------------------------------------------------------------
------------------------------------------------------------------------------
``` 

On peut très bien régénèrer une nouvelle requête : 

```sql
SELECT ville, COUNT(*) AS "nombre de commandes", SUM(montant) AS "Pour un total de" 
FROM stream_commandes
WINDOW TUMBLING (SIZE 1 MINUTE)
GROUP BY ville
EMIT CHANGES;
``` 

