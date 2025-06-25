import time
import json
import random
import os
from confluent_kafka import Producer

villes = ["Paris", "Lyon", "Toulouse", "Marseille"]

#producer = Producer({'bootstrap.servers': 'kafka:9092'})
producer = Producer({
    'bootstrap.servers': os.getenv('BOOTSTRAP_SERVERS', 'redpanda:9092')
})

def generer_commande():
    return {
        "ville": random.choice(villes),
        "montant": round(random.uniform(10, 100), 2),
        "ts": int(time.time() * 1000)
    }

while True:
    commande = generer_commande()
    producer.produce("commandes", key=commande["ville"], value=json.dumps(commande))
    producer.flush()
    print("Envoyé :", commande)
    time.sleep(1)
