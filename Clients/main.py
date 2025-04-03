import flwr as fl
import tensorflow as tf
import socket
from utils import local_evaluate, logging, create_model
import loadProcData 
import logging
import time
from kubernetes import client as clt, config
from ClassClient import ClientDP
from ClassClient import ClientNFStream
from ClassClient import ClientZKP
from ClassClient import ClientZKPAndDP
import schedule 
import numpy as np 
import pandas as pd
from getpass import getpass
from noknow.core import ZK, ZKSignature, ZKParameters, ZKData, ZKProof
from queue import Queue
from multiprocessing import Process
from threading import Thread
from secrets import token_hex
import pickle
from enum import Enum
import json
import tracemalloc
import paho.mqtt.client as mqtt

class ClientType(Enum):
    NONE = 1
    ZKP = 2
    DP = 3
    BOTH = 4

def get_ip_server():
    #use kubernetes API
    config.load_incluster_config()
    # Give it few seconds to load cluster configuration and initialize aggregator
    time.sleep(5)
    logging.info("ESTOU")
    v1 = clt.CoreV1Api()
    podList = v1.list_namespaced_service(namespace="default")
    logging.info(podList)
    for pod in podList.items:
        if "server-service" in pod.metadata.name:
            serverPod = pod
            print(serverPod)
        break
    server_ip = serverPod.status.load_balancer.ingress[0].ip
    logging.info(serverPod.status)
    return server_ip

def get_client_type():
    logged_waiting_message = False
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect(('0.0.0.0', 4040))
                logging.info("Connected to server to get client type")
                data = client_socket.recv(1024)
                if data:
                    flag = pickle.loads(data)
                    logging.info(f"Received client type: {ClientType(flag).name}")
                    return ClientType(flag)
                else:
                    if not logged_waiting_message:
                        logging.warning("No data received, waiting...")
                        logged_waiting_message = True
                    time.sleep(5)
        except Exception as e:
            logging.error(f"Error while trying to get client type from the server: {str(e)}")
            time.sleep(5)      
        finally:
            if logged_waiting_message:
                logging.info("Retrying connection...")
                logged_waiting_message = False   

def send_parameters(model, threshold, current, peak, time_spent):
    try:
        parameters= model.get_weights()
        dfParameters = pd.DataFrame.from_records(parameters)
        dfJson = dfParameters.to_json(orient='records')
        dataDict = {
            "parameters" : json.loads(dfJson),
            "threshold" : threshold,
            "current" : current,
            "peak" : peak,
            "time" : time_spent
        }
        
        # Configura el cliente MQTT
        client = mqtt.Client()
        client.connect("emqx-deployment", 1883, 60)
        client.loop_start()
        
        client.publish("receive_parameters", json.dumps(dataDict))
        client.loop_stop()
        client.disconnect()
               
    except Exception as e:
        logging.error(f"exception while trying to send the data to the server: {str(e)}")    
              
def connect_server(model, flag):
    try:
        logging.info(flag)

        if flag == ClientType.NONE:
            client = ClientNFStream(model)
            logging.info("1")
        elif flag == ClientType.ZKP:
            client = ClientZKP(model)
            logging.info("2")
        elif flag == ClientType.DP:
            client = ClientDP(model)
            logging.info("3")
        elif flag == ClientType.BOTH:
            client = ClientZKPAndDP(model)
            logging.info("4")
        else:
            logging.error("Unknow client type received")
                
        # Start Flower client
        ip_address = "0.0.0.0"
        server_address_connect=ip_address + ':8080'
        
        time_begin = time.time()
        tracemalloc.start()
        fl.client.start_client(server_address=server_address_connect, client=client.to_client())
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        time_end = time.time()
        time_spent = time_end - time_begin
        send_parameters(model, client.threshold, current, peak, time_spent)
                
    except Exception as e:
        logging.error(f"Error while trying to connect to the server: {str(e)}")

def create_process_server(model, flag):
    connect_server_process = Process(target=connect_server, args=(model, flag))
    connect_server_process.start()
    connect_server_process.join()

def create_process_evaluate(model):
    local_evaluate_process = Process(target=local_evaluate, args=(model,))
    local_evaluate_process.start()
    local_evaluate_process.join()
    
def connectZKP():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(('0.0.0.0', 6060))
            logging.info("Generating keys...")
            client_zk = ZK.new(curve_name="secp256k1", hash_alg="sha3_256")
            password = token_hex(16)
            # Create signature and send to server
            logging.info("creating signature...")
            signature = client_zk.create_signature(password).dump()
            logging.info("sending signature...")
            client_socket.send(pickle.dumps(signature))
            # Receive the token from the server
            logging.info("receiving token...")
            #token = client_socket.recv(1048576).decode()
            token = pickle.loads(client_socket.recv(1048576))            
            # Create a proof that signs the provided token and sends to server
            logging.info("signing proof...")
            proof = client_zk.sign(password, token).dump()
            # Send the token and proof to the server
            logging.info("sending proof...")
            client_socket.send(pickle.dumps(proof))
            logging.info("receiving response...")
            server_response = pickle.loads(client_socket.recv(1048576))
            if server_response == "True":
                logging.info("Zero-Knowledge Proof successful! Receiving flag...")
                flag = pickle.loads(client_socket.recv(1048576))  # Receive the flag from the server
                logging.info(f"Received flag: {ClientType(flag).name}")
                return True            
            else:
                raise Exception("Zero-Knowledge Proof failed. Training aborted.")
    except Exception as e:
        logging.error(f"Error while trying to connect to the server ZKP: {str(e)}")
        return False

def main():
    logging.basicConfig(level=logging.INFO)
    dfNormalized, dfNormalizedTest = loadProcData.load_and_preprocess_data()
    model = create_model(dfNormalized)
    try:
        flag = get_client_type()
        if flag in [ClientType.ZKP, ClientType.BOTH]:
            if not connectZKP():
                return
        schedule.every(30).seconds.do(create_process_server, model, flag)
    except Exception as e:
        logging.error(f"Failed to initialize client: {str(e)}")

    while True:
        schedule.run_pending()
        time.sleep(1)    
    
if __name__ == "__main__":
    main()


