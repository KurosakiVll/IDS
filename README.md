🔒 Federated Learning-Based Cybersecurity for Intrusion Detection System 🚀

This repository contains an experimental project focused on cybersecurity in networks and intrusion detection system using Federated Learning approaches in Python. 
The goal is to improve detection of anomalies, protect user privacy, and simplify large-scale deployments. The project leverages advanced techniques such as Differential Privacy
Zero-Knowledge Proofs and container orchestration (Docker & Kubernetes) to ensure robust, private and scalable solutions

🔎 Overview
In modern distributed systems, transferring raw data to a central server can be inefficient and may compromise privacy. 
Federated Learning addresses these challenges by enabling machine learning model training directly on client devices or local servers, sending back only model updates. This project augments such a learning paradigm with:
  
  ⚖️ Differential Privacy – Adds calibrated noise to safeguard individual data.

  🕵️ Zero-Knowledge Proofs – Validates contributions without revealing sensitive details.

  💬 Lightweight Communication (MQTT) – For message-based data exchange.

  🐳 Docker & ☸️ Kubernetes – For efficient containerization and orchestration

The end goal is to detect network intrusions or security anomalies with minimal privacy risks and scalable deployment.

⭐️ Features

  🤝 Federated Training: Aggregates model parameters from multiple nodes without exposing raw data.

  🔐 Privacy Enhancements: Incorporates Differential Privacy and Zero-Knowledge Proof to ensure confidentiality.

  🔧 Modular Architecture: Separate components (Client, Server, Collector, Generator) for easy maintenance and extension.

  📦 Containerized Deployments: Uses Docker for containerization and Kubernetes for high-scale orchestration.

  📡 Scalable Communication: Employs MQTT for distributing updates and collecting real-time system logs

⚙️ Technologies Used

  🐍 Python (3.8+ recommended)

  🧠 TensorFlow (federated model training)

  🌸 Flower (Federated Learning framework)

  🐳 Docker (containerization)

  ☸️ Kubernetes (orchestration; optional but recommended for scaling)

  💬 MQTT (e.g., Eclipse Mosquitto)

  🗄️ SQLite or similar (lightweight database for server logs)

🔒 Security/Privacy Tooling

  ⚖️ Differential Privacy (via TensorFlow Privacy or custom implementation)

  🕵️ Zero-Knowledge Proofs (e.g., pyZKP or another cryptography library)

🏗️ Installation and Setup

  pip install -r requirements.txt

The requirements.txt likely includes:

  tensorflow (or tensorflow-gpu)

  tensorflow-privacy

  flower

  paho-mqtt

  cryptography (or zero-knowledge proof library)

Docker build (optional if you want to run everything in containers):

  docker build -t federated-cybersecurity

Kubernetes deployment:

  Modify the Kubernetes YAML manifest files (e.g., deployment.yaml, service.yaml) as needed.

  Apply them to your cluster:

  kubectl apply -f deployment.yaml  

MQTT Broker:

  Install and configure Eclipse Mosquitto or another broker.

  Update broker credentials and addresses in the project’s configuration files 

🚦 Usage (Basic Flow)

  Start the Server: Aggregates incoming client updates and orchestrates training.

  Launch Clients: Each client trains locally on its own dataset, then sends updates (not raw data) to the server.

Collector & Generator:

  Collector: Gathers logs/telemetry for extended analysis or anomaly detection.

  Generator: Produces synthetic data/traffic to test or demo intrusion detection.


Author:

KurosakiVll

FullStack Developer | Cybersecurity Technician
  
