


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