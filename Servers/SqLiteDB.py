import flwr as fl
import tensorflow as tf
import paho.mqtt.client as mqtt
import json
import sqlite3
import logging

# Crear la tabla en la base de datos SQLite para almacenar los pesos del modelo
def createDb():
    connection = sqlite3.connect(DATABASE_NAME)
    cur = connection.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS client_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    weights TEXT,
                    threshold REAL,
                    current REAL,
                    peak REAL,
                    time REAL
                  )''')
    connection.commit()
    connection.close()

# Insertar los pesos del modelo en la base de datos SQLite
def insert_model_weights(weights, threshold, current, peak, time_spent):
    conn = sqlite3.connect('model_weights.db')
    c = conn.cursor()
    c.execute("INSERT INTO model_weights (weights, threshold, current, peak, time_spent) VALUES (?,?,?,?,?)",
              (json.dumps(weights), threshold, current, peak, time_spent))   
    conn.commit()
    conn.close()

# MQTT callback functions
def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected with result code {rc}")
    client.subscribe("receive parameters")
   
def on_message (client, userdata, msg):
    try:
        data = json.loads(msg.payload)
        insert_model_weights(data['parameters'], data['threshold'], data['current'], data['peak'], data['time'])
        logging.info("Data inserted into the database successfully.")   
    except Exception as e:
        logging.info(f"Failed to insert data: {str(e)}")
        
        