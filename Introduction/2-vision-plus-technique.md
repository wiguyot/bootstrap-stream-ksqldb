# introduction à Kafka Streams et ksqldb


## Partie 2 – Vision plus technique


### Kafka Streams 

Kafka Streams est une bibliothèque cliente Java/Scala (mais pilotable depuis Python via des producteurs/consommateurs).

    Elle permet de créer des applications distribuées de traitement de flux sans serveur (pas besoin de Spark, Flink ou cluster).

**Chaque application Kafka Streams est un consumer group qui peut faire**  :

        Stateless transformations : map, filter, flatMap

        Stateful operations : aggregate, join, windowed count avec rocksDB local + changelog Kafka

**Architecture** :

    KStream : flux d’événements (ligne par ligne, comme une table de logs).

    KTable : vue dédupliquée (par clé), comme une table SQL.

    GlobalKTable : table partagée partout.

### Exemple (côté Python simulé avec confluent_kafka pour produire/consommer) :

Supposons que l’on produise ça dans un topic commandes :

```python
from confluent_kafka import Producer
import json, time

p = Producer({'bootstrap.servers': 'localhost:9092'})
while True:
    event = {"ville": "Lyon", "montant": 50, "ts": int(time.time() * 1000)}
    p.produce("commandes", key="Lyon", value=json.dumps(event))
    p.flush()
    time.sleep(1)
````

Et dans Kafka Streams, on pourrait faire :

    Regroupement par ville

    Fenêtrage par minute

    Comptage

### Fenêtres temporelles :

Kafka Streams (et ksqlDB) propose plusieurs types de fenêtres :

| Type     | Description                                   |
|----------|-----------------------------------------------|
| Tumbling | Fenêtre fixe / Fenêtre sans chevauchement     |
| Hopping  | Fenêtre à chevauchement                       |
| Sliding  | Fenêtre glissante.                            |
| Session  | Basée sur l’inactivité (temps sans événement) |


### ksqlDB – SQL sur flux Kafka

✔️ Fonctionnement :

    CREATE STREAM pour consommer un topic Kafka comme une table infinie

    EMIT CHANGES pour garder la requête ouverte et voir les données évoluer

    Chaque requête est matérialisée (stateful) avec un état local, fenêtrée, etc.

🧪 Exemple complet :

1. Créer une stream depuis le topic

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
```
2. Compter par ville toutes les minutes

```sql
SELECT ville, COUNT(*) 
FROM commandes
WINDOW TUMBLING (SIZE 1 MINUTE)
GROUP BY ville
EMIT CHANGES;
```

➡️ Cela produit un flux de résultats qui ressemble à une table SQL, mais évolutive dans le temps.


🔒 Stateful vs Stateless – Impact concret

| Aspect         | Stateless                          | Stateful                                         |
|----------------|------------------------------------|--------------------------------------------------|
| Opérations     | map, filter                        | join, aggregate, windowed count                  |
| Complexité     | Faible                             | Doit gérer le state store local + Kafka changelog |
| Consommation   | Peu de mémoire                     | Besoin de disques + sauvegarde                   |
| Cas typiques   | Nettoyage, filtrage                | Agrégation, enrichissement (lookup table)        |


## À retenir : 


**Kafka Streams et ksqlDB sont complémentaires :** l’un pour les **développeurs**, l’autre pour les **analystes**.

**ksqlDB repose sur Kafka Streams** en interne.

**ksqlDB peut être piloté via REST API** donc il y a une grande indépendance et pluralité dans le choix des outils ou langages pour : 
- produire
- requêter en SQL
- consommer 