# TP — Traitement de flux avec ksqlDB (pas à pas, pédagogique)

Ce TP te fait pratiquer **les fondamentaux de ksqlDB** : création de streams/tables, clés et (re)partitionnement, fenêtres (tumbling/hopping), agrégations, **PUSH vs PULL queries**, **JOIN** stream‑table, introspection et nettoyage.  
Exemple fil rouge : un flux de températures par ville publié dans Kafka (`temperatures`).

---

## 0) Prérequis et points d’accès

- **Docker + Docker Compose** opérationnels.
- Un **cluster Kafka** et **ksqlDB** démarrés par ta stack (ports typiques : Kafka `9092`, ksqlDB REST `8088`).  
  > Adapte les hôtes/ports ci‑dessous à **ta** stack (noms de services Compose, etc.).

Définis deux variables d’environnement (macOS/Linux) pour fluidifier les commandes :

```bash
export BROKER="<host:port Kafka>"

# Exemple si tu es dans un réseau Docker compose :
# export BROKER="kafka-1:9092"
export KSQLDB_URL="http://<host:port ksqldb>"
# Exemple :
# export KSQLDB_URL="http://ksqldb:8088"
```

Vérifie que ksqlDB répond :

```bash
curl -s "$KSQLDB_URL/info" | jq .
# ou
curl -s "$KSQLDB_URL/healthcheck"
```

Les éléments attendus sont de l'ordre de : 

```yaml
prompt : curl -s "$KSQLDB_URL/info" | jq .

{
  "KsqlServerInfo": {
    "version": "0.27.2",
    "kafkaClusterId": "une certaine valeur aléatoire",
    "ksqlServiceId": "ksql_kraft",
    "serverStatus": "RUNNING"
  }
}

prompt : curl -s "$KSQLDB_URL/healthcheck"

{"isHealthy":true,"details":{"metastore":{"isHealthy":true},"kafka":{"isHealthy":true},"commandRunner":{"isHealthy":true}}}%  
```

---

## 1) Création du topic source + envoi de données de test

Crée le topic `temperatures` (4 partitions par exemple) :

```bash
# Avec kafka-topics (dans un conteneur Kafka si nécessaire)
docker exec -i kafka-1 \
  kafka-topics --bootstrap-server "$BROKER" \
  --create --topic temperatures --partitions 4 --replication-factor 1 --if-not-exists
```

- Ecris la commande qui va bien pour vérifier le bon fonctionnement de la commande précédente.

- Publie des événements JSON (clé = ville, valeur = {ville, t, ts}) :

```bash
# Option - kafka-console-producer (clé via parse.key)
bash -lc 'python3 - <<'"'"'PY'"'"' | docker exec -i kafka-1 \
  kafka-console-producer --bootstrap-server '"$BROKER"' \
  --topic temperatures --property parse.key=true --property key.separator=:
import json,random,time,sys
villes=["Clermont-Ferrand","Lyon","Paris","Bordeaux","Nantes"]
for _ in range(100):
    v=random.choice(villes)
    rec={"ville":v,"t":round(random.uniform(5,35),1),"ts":int(time.time()*1000)}
    print(f"{v}:{json.dumps(rec)}"); sys.stdout.flush(); time.sleep(0.2)
PY'
```

- Ouvrez un navigateur sur l'URL du control-center et montrez le remplissage du topic **temperatures**. Montrez la répartition des messages au travers des partitions. 

Contrôle rapide du topic :

```bash
docker exec -i kafka-1 \
  kafka-topics --bootstrap-server "$BROKER" --describe --topic temperatures
```

- Maintenant changez légèrement le code python précédent par 

```bash
# Option - kafka-console-producer (clé via parse.key)
bash -lc 'python3 - <<'"'"'PY'"'"' | docker exec -i kafka-1 \
  kafka-console-producer --bootstrap-server '"$BROKER"' \
  --topic temperatures --property parse.key=true --property key.separator=:
import json,random,time,sys
villes=["Clermont-Ferrand","Lyon","Paris","Bordeaux","Montpellier"]
for _ in range(200):
    v=random.choice(villes)
    rec={"ville":v,"t":round(random.uniform(5,35),1),"ts":int(time.time()*1000)}
    print(f"{v}:{json.dumps(rec)}"); sys.stdout.flush(); time.sleep(0.2)
PY'
```

Qu'observez vous sur la répartition des messages ? 

Intéressez vous à la fonction de hachage Murmur2. Quel est son lien avec notre affaire ? 

---

## 2) Se connecter à ksqlDB

Trois options (au choix) :

- **CLI intégré** :
  ```bash
  ksql "$KSQLDB_URL"
  ```
- **UI Web** (si exposée par ta stack) : ouvre `http(s)://<host>:<port>/` et passe en mode ksql.
- **REST** (utilisé plus bas) : `POST $KSQLDB_URL/ksql` ou `/query-stream`.

---

## 3) Définir le schéma source et (re)partir par clé

**Important** : en ksqlDB, la **clé logique** (KEY) gouverne les agrégations/joints.  
Même si la valeur contient `ville`, **il faut s’assurer que la clé Kafka = ville**.

1. **Stream brut** mappé sur le topic :

```sql
CREATE STREAM S_TEMPS_RAW (
  ville STRING,
  t DOUBLE,
  ts BIGINT
) WITH (
  KAFKA_TOPIC = 'temperatures',
  VALUE_FORMAT = 'JSON',
  TIMESTAMP = 'ts'
);
```

2. **Repartitionnement par ville** (on définit la clé = `ville`) :

```sql
CREATE STREAM S_TEMPS_BY_VILLE
  WITH (KAFKA_TOPIC='temperatures_by_ville', PARTITIONS=4) AS
SELECT ville, t, ts
FROM S_TEMPS_RAW
PARTITION BY ville
EMIT CHANGES;
```

Vérifie :

```sql
SHOW STREAMS;
DESCRIBE EXTENDED S_TEMPS_BY_VILLE;
```

Astuce :  
```sql
PRINT 'temperatures' FROM BEGINNING LIMIT 5;
PRINT 'temperatures_by_ville' FROM BEGINNING LIMIT 5;
```

---

## 4) Fenêtres et agrégations (TUMBLING)

Créons une table matérialisée des **maxima 5 minutes** par ville :

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

**PUSH query** (flux continu des mises à jour) :

```sql
-- Affiche en continu les fenêtres qui se remplissent
SELECT * FROM T_MAX_5M EMIT CHANGES;
```

> Remarque : les tables **fenêtrées** sont idéales en PUSH.  
> Pour du PULL, préfère une table **non fenêtrée** (voir §5).

---

## 5) PULL vs PUSH queries (dernière valeur par ville)

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

- **PULL query** (requête ponctuelle par clé **exacte**) :

```sql
-- Exemple : récupère la dernière température pour Lyon
SELECT t_last, ts_last FROM T_LAST WHERE ville='Lyon';
```

- **PUSH query** (abonnement) :

```sql
SELECT ville, t_last, ts_last FROM T_LAST EMIT CHANGES;
```

---

## 6) JOIN Stream‑Table (enrichissement)

1. Prépare une **table de référence** (pays, altitude, etc.).  
   Crée un topic `cities` et publie quelques lignes clé=ville :

```bash
python - <<'PY' | kafka-console-producer \
  --bootstrap-server "$BROKER" \
  --topic cities \
  --property parse.key=true \
  --property key.separator=:
import json
rows = [
  ("Clermont-Ferrand", {"pays":"FR","alt_m": 410}),
  ("Lyon",              {"pays":"FR","alt_m": 170}),
  ("Paris",             {"pays":"FR","alt_m": 35}),
  ("Bordeaux",          {"pays":"FR","alt_m": 6}),
  ("Nantes",            {"pays":"FR","alt_m": 18}),
]
for k,v in rows:
    print(f"{k}:{json.dumps({'ville':k, **v})}")
PY
```

2. Déclare la **TABLE** côté ksqlDB (clé = ville) :

```sql
CREATE TABLE CITIES (
  ville STRING PRIMARY KEY,
  pays  STRING,
  alt_m INT
) WITH (
  KAFKA_TOPIC = 'cities',
  KEY_FORMAT  = 'KAFKA',
  VALUE_FORMAT= 'JSON'
);
```

3. **JOIN** : enrichir le flux des températures par les métadonnées ville :

```sql
CREATE STREAM S_TEMPS_ENRICH AS
SELECT
  s.ville,
  c.pays,
  c.alt_m,
  s.t,
  s.ts
FROM S_TEMPS_BY_VILLE s
LEFT JOIN CITIES c
  ON s.ville = c.ville
EMIT CHANGES;
```

Vérifie :
```sql
SELECT * FROM S_TEMPS_ENRICH EMIT CHANGES LIMIT 10;
```

---

## 7) HOPPING windows (option)

Fenêtres glissantes de 10 min, **pas** de 2 min :

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

---

## 8) Introspection, statut et plan d’exécution

```sql
SHOW TOPICS;
SHOW TABLES;
SHOW QUERIES;

DESCRIBE EXTENDED T_MAX_5M;
EXPLAIN CSAS_T_T_MAX_5M_...;  -- Remplace par l’ID réel de la requête
```

Côté REST (exemple) :

```bash
curl -s -X POST "$KSQLDB_URL/ksql" \
  -H 'Content-Type: application/vnd.ksql.v1+json; charset=utf-8' \
  -d '{"ksql":"SHOW STREAMS;","streamsProperties":{}}'
```

---

## 9) Critères de réussite

- `DESCRIBE EXTENDED` pour chaque objet est **cohérent** (schéma, formats).
- Les tables matérialisées **évoluent** quand de nouvelles données arrivent.
- Tu as démontré **PULL** (sur `T_LAST`) **et** **PUSH** (sur tables fenêtrées).
- Le **JOIN** enrichit bien le flux (pays, altitude).
- Tu sais **(re)partitioner** par `ville` pour des agrégations correctes.
- Un script `.sql` **reproductible** (création puis drop) fonctionne de bout en bout.

---

## 10) Nettoyage

Dans le CLI ksqlDB :

```sql
SHOW QUERIES;
TERMINATE <QUERY_ID>;          -- pour chaque requête en cours

DROP STREAM IF EXISTS S_TEMPS_ENRICH DELETE TOPIC;
DROP TABLE  IF EXISTS T_AVG_10M_HOP2 DELETE TOPIC;
DROP TABLE  IF EXISTS T_MAX_5M DELETE TOPIC;
DROP TABLE  IF EXISTS T_LAST DELETE TOPIC;
DROP STREAM IF EXISTS S_TEMPS_BY_VILLE DELETE TOPIC;
DROP STREAM IF EXISTS S_TEMPS_RAW;   -- sans DELETE TOPIC si partagé

-- Optionnel, côté Kafka :
-- kafka-topics --bootstrap-server "$BROKER" --delete --topic temperatures
-- kafka-topics --bootstrap-server "$BROKER" --delete --topic cities
-- kafka-topics --bootstrap-server "$BROKER" --delete --topic temperatures_by_ville
```

---

## 11) Pièges fréquents & bonnes pratiques

- **Clé manquante** : si tes agrégations ne sortent rien, (re)partitions par la bonne clé :
  ```sql
  ... FROM <stream> PARTITION BY ville EMIT CHANGES;
  ```
- **Timestamp** : si tu as des fenêtres vides, assure‑toi d’avoir `TIMESTAMP='ts'` ou un champ temporel correct.
- **PULL queries** : uniquement sur **TABLES** et avec **clé exacte** (pas de `LIKE`/`>`).
- **Late events** : utilise `GRACE PERIOD` dans les fenêtres si des événements arrivent en retard.
- **Formats** : JSON suffit pour le TP. Avec Avro/Schema Registry, pense aux schémas évolutifs.
- **Observabilité** : `PRINT <topic>` est ton ami pour déboguer.

---

## 12) Pour aller plus loin (exercices)

1. Ajoute une **détection d’anomalies** : `WHERE t NOT BETWEEN -30 AND 55`.
2. Calcule un **z‑score** par ville sur une fenêtre glissante et alerte si `|z| > 3`.
3. Matérialise un **TOP‑N** des villes les plus chaudes sur 30 min (fenêtres HOPPING).
4. Expose les dernières valeurs via **PULL** (script REST cURL) pour une intégration dashboard.

