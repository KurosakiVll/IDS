import flwr as fl
import tensorflow as tf
import logging
import socket
import schedule
import time
from getpass import getpass
from noknow.core import ZK, ZKSignature, ZKParameters, ZKData, ZKProof
from queue import Queue
from threading import Thread
from multiprocessing import Process
import pickle
from secrets import token_hex
from enum import Enum
import SqLiteDB
import json
import paho.mqtt.client as mqtt

DATABASE_NAME = "database.db"

class ClientType(Enum):
    NONE = 1
    ZKP = 2
    DP = 3
    BOTH = 4

def select_client_type():
    print("Select client type:")
    print("1. None")
    print("2. ZKP")
    print("3. DP")
    print("4. BOTH")
    choice = int(input("Enter the number of the client type: ")) # passar a variable ambiente.           
    return ClientType(choice)

def define_strategy():
    return fl.server.strategy.FedAvg(min_available_clients=1, min_fit_clients=1, min_evaluate_clients=1)
	
def start_federated_round():
    connect_process = Process(target=start_flower_server)
    connect_process.start() 

def start_flower_server():
    try:
        ip_address = socket.gethostbyname((socket.gethostname()))
        server_address=ip_address + ':8080'
        logging.info(server_address)
        
        # Start Flower Server 
        fl.server.start_server(
            server_address=server_address,
            config=fl.server.ServerConfig(num_rounds=1),
            strategy = define_strategy()
        )
                    
    except Exception as e:
        logging.error("Exception while receiving the clients: " + str(e))

def wait_option(flag_option):
    logging.info("waiting for clients...")
    # Receive proof from client
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(('0.0.0.0', 4040))
            server_socket.listen()
            while True:
                connection, address = server_socket.accept()
                logging.info("CLIENT CONNECTED")
                process = Process(target=handle_client_option, args=(connection, flag_option))
                process.start()
    except Exception as e:
        logging.error("Error in serverZKP: " + str(e))

def handle_client_option(connection, flag_option):
    with connection:
        try:
            logging.info(f"Sending client type: {ClientType(flag_option).name}")
            connection.send(pickle.dumps(flag_option.value))
        except Exception as e:
            logging.error("Error handle client option: " + str(e))
            
def serverZKP(flag_option):
    logging.info("FUNCTION SEVERZKP")
    # Receive proof from client
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(('0.0.0.0', 6060))
            server_socket.listen()
            while True:
                connection, address = server_socket.accept()
                logging.info("CLIENT CONNECTED")
                process = Process(target=handle_client, args=(connection,flag_option))
                process.start()
    except Exception as e:
        logging.error("Error in serverZKP: " + str(e))

# Función para manejar la conexión de un cliente
def handle_client(connection, flag_option):
    with connection:
        try: 
            # Set up server component
            logging.info("generating key server...")
            password = token_hex(16)
            server_zk = ZK.new(curve_name="secp384r1", hash_alg="sha3_512")
            server_signature: ZKSignature = server_zk.create_signature(password)
            # Load the received signature from the Client
            logging.info("receiving signature...")
            sig = pickle.loads(connection.recv(1048576))
            logging.info("descerializing siganture...")
            client_signature = ZKSignature.load(sig)
            logging.info("creating zk client...")
            client_zk = ZK(client_signature.params)
            # Create a signed token and send to the client
            logging.info("creating token...")
            token = server_zk.sign(password, client_zk.token())
            logging.info("sending token...")
            #connection.send(token.dump(separator=":").encode())
            connection.send(pickle.dumps(token.dump(separator=":")))
            # Get the token from the client
            logging.info("getting proof...")
            proof = ZKData.load(pickle.loads(connection.recv(1048576)))
            logging.info("getting proof...")
            token = ZKData.load(proof.data, ":")
            # the server signs the token so it can be sure it has not been modified
            if not server_zk.verify(token, server_signature):
                logging.info("aborting...")
                connection.send(pickle.dumps("False"))
            else:
                logging.info("verifying......")
                if client_zk.verify(proof, client_signature, data=token):
                    connection.send(pickle.dumps("True"))
                    logging.info("sending flag...")
                    connection.send(pickle.dumps(flag_option.value))
                else:    
                    connection.send(pickle.dumps("False"))
        except Exception as e:
            logging.error("Error while processing client data: " + str(e))
            connection.send(pickle.dumps("False"))

def main():
    logging.basicConfig(level=logging.INFO)
    SqLiteDB.createDb()
    flag_option = select_client_type()
    
    server_option_process = Process(target= wait_option, args=(flag_option,))
    server_option_process.start()
    server_zkp_process = Process(target=serverZKP, args=(flag_option,))
    server_zkp_process.start()
    
    # Configura el cliente MQTT
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = SqLiteDB.on_connect
    mqtt_client.on_message = SqLiteDB.on_message
    mqtt_client.connect("emqx-deployment", 1883, 60)
    mqtt_client.loop_start()
    
    start_federated_round()
    schedule.every(5).minutes.do(start_federated_round)

    while True:
        schedule.run_pending()
        time.sleep(1)
    
if __name__ == "__main__":
    main()
        
    