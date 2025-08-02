## BITS Pilani Thesis
Decentralised machine learning Simulation on GCP

## Architecture
![alt text](<resources/doc/BITS Multi porject architecture.jpg>)

- The GCP infra is build in 2 different projects as part of multi pod interactions
- Github actions are used for the CI/CD pipeline
- The code is dockerized and pushed to GCP Artifactory/Registry
- The projects would pick the image from the respective artifactories in their projects
- Few of teh infra setup is automated with Terrafrom scripts whereas few are pening like VPC creation and firewall rule changes


Few other commands which are used:
#### IP Creation for nodes
```
for i in {0..4}; do
  gcloud compute addresses create iot-$i-ip-central \
    --region=us-central \
    --subnet=us-central-subnet \
    --addresses=10.10.0.1$((i+0)) \
    --purpose=GCE_ENDPOINT ;
done
```

#### GCP Connecting
```
Project 1
gcloud container clusters get-credentials autopilot-cluster-a \
  --region us-central1 \
  --project bits-dissertation-464410

Project2: 
gcloud container clusters get-credentials autopilot-cluster-b \
  --region us-central1 \
  --project bits-project-465110
```

#### DNS record additions:
```
gcloud dns record-sets transaction start --zone=iot-central-zone

gcloud dns record-sets transaction add 10.10.0.10 \
  --name="iot-node-0.central.iot.svc.cluster.local." \
  --ttl=60 --type=A --zone=iot-central-zone

gcloud dns record-sets transaction add 10.10.0.11 \
  --name="iot-node-1.central.iot.svc.cluster.local." \
  --ttl=60 --type=A --zone=iot-central-zone

gcloud dns record-sets transaction add 10.10.0.12 \
  --name="iot-node-2.central.iot.svc.cluster.local." \
  --ttl=60 --type=A --zone=iot-central-zone

gcloud dns record-sets transaction add 10.10.0.13 \
  --name="iot-node-3.central.iot.svc.cluster.local." \
  --ttl=60 --type=A --zone=iot-central-zone

gcloud dns record-sets transaction add 10.10.0.14 \
  --name="iot-node-4.central.iot.svc.cluster.local." \
  --ttl=60 --type=A --zone=iot-central-zone

gcloud dns record-sets transaction execute --zone=iot-central-zone


# EAST#######

gcloud dns record-sets transaction start --zone=iot-east-zone

gcloud dns record-sets transaction add 10.20.0.10 \
  --name="iot-node-0.east.iot.svc.cluster.local." \
  --ttl=60 --type=A --zone=iot-central-zone

gcloud dns record-sets transaction add 10.20.0.11 \
  --name="iot-node-1.east.iot.svc.cluster.local." \
  --ttl=60 --type=A --zone=iot-central-zone

gcloud dns record-sets transaction add 10.20.0.12 \
  --name="iot-node-2.east.iot.svc.cluster.local." \
  --ttl=60 --type=A --zone=iot-central-zone

gcloud dns record-sets transaction add 10.20.0.13 \
  --name="iot-node-3.east.iot.svc.cluster.local." \
  --ttl=60 --type=A --zone=iot-central-zone

gcloud dns record-sets transaction add 10.20.0.14 \
  --name="iot-node-4.east.iot.svc.cluster.local." \
  --ttl=60 --type=A --zone=iot-central-zone

gcloud dns record-sets transaction execute --zone=iot-east-zone
```

### Port forwarding commands for debugging
```
kubectl port-forward svc/prometheus-service 9090:9090
kubectl port-forward pod/iot-node-0 8000:8000
```

### Grafana link
http://34.59.88.18:3000/