# TP — Traitement de flux avec ksqlDB

## Objectifs
- Créer **streams/tables**, faire **agrégations** (fenêtres TUMBLING/HOPPING).
- Construire une **vue matérialisée** (PULL/PUSH queries).
- Réaliser un **JOIN** stream-table.

## Prérequis
- Docker + Docker Compose.
- Accès :
  - ksqlDB server/UI : `http://<HOST>:<KSQLDB_PORT>`  <!-- TODO -->
  - Broker : `<KAFKA_BROKER_HOST>:<KAFKA_BROKER_PORT>`  <!-- TODO -->
  - Topic source (ex. `temperatures`).

## Démarrage rapide
```bash
git clone <ce dépôt>
cd bootstrap-stream-ksqldb
docker compose up -d
# Accéder à ksqlDB (CLI ou UI selon ta stack)
````

## TP pas à pas

	1.	Stream source :

```sql
CREATE STREAM S_TEMPS (
  ville STRING KEY,
  t DOUBLE,
  ts BIGINT
) WITH (KAFKA_TOPIC='temperatures', VALUE_FORMAT='JSON');
```

	2.	Agrégation par fenêtre :

```sql
CREATE TABLE T_MAX AS
SELECT ville,
       WINDOWSTART AS w_start,
       MAX(t) AS t_max
FROM S_TEMPS
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY ville
EMIT CHANGES;
```

	3.	Exécuter PUSH query sur S_TEMPS et PULL query sur T_MAX.
	4.	(Option) Charger table de ref CITIES et faire un JOIN.

## Critères de réussite
	•	DESCRIBE EXTENDED OK.
	•	Vue agrégée évolutive (nouvelles données → mise à jour).
	•	Script .sql reproductible (création + drop).