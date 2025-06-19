# Mise en oeuvre ksqldb

## Objectifs pédagogiques

- Produire un flux de commandes en Python
- Consommer ce flux avec ksqlDB (CREATE STREAM, WINDOW TUMBLING)
- Visualiser les résultats en direct dans un terminal

## Production de l'infra docker

Dans le répertoire courant (1-illustration) on va pouvoir trouver
- le docker-compose.yml à lancer => docker compose up --build

On pourra lancer un terminal sur le container ksql

```bash
docker-compose run cli ksql http://ksqldb:8088
```

puis exécuter les requêtes : 

```sql
CREATE STREAM commandes (
  ville VARCHAR,
  montant DOUBLE,
  ts BIGINT
) WITH (
  KAFKA_TOPIC='commandes',
  VALUE_FORMAT='JSON',
  TIMESTAMP='ts'
);

SELECT ville, COUNT(*) 
FROM commandes
WINDOW TUMBLING (SIZE 1 MINUTE)
GROUP BY ville
EMIT CHANGES;
``` 