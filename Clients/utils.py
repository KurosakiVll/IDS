import flwr as fl
import numpy as np
import pandas as pd
import tensorflow as tf
from nfstream import NFStreamer
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, StandardScaler
from tensorflow_privacy.privacy.optimizers.dp_optimizer import DPAdamOptimizer
from tensorflow_privacy.privacy.optimizers.dp_optimizer import DPGradientDescentGaussianOptimizer
from tensorflow_privacy.privacy.optimizers.dp_optimizer import DPAdamGaussianOptimizer
from tensorflow.keras.optimizers import Optimizer
import time
import socket
from kubernetes import client as clt, config
import loadProcData
import logging

def training_values():
    # Definires os dados de treino e proba
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
    x_train, x_test = x_train / 255.0, x_test / 255.0
    return x_train, y_train, x_test, y_test

def local_evaluate(model):
    try:
        inputTest = loadProcData.load_and_preprocess_data()
        reconstructed = model.predict(inputTest)
        mae = np.mean(np.abs(inputTest - reconstructed), axis=1)
        
        predictions = (mae > 0.5).astype(int)

        rowsToDrop = [i for i,val in enumerate(predictions) if val != 0]
        if len(rowsToDrop) > 0 :
            df = pd.read_csv('/shared-data/out.csv')
            for id, row in enumerate(rowsToDrop):
                logging.info("POTENTIAL ATTACK DETECTED!")
                logging.info("Removing it from the CSV")
                df.drop(index=row, inplace=True)
            df.to_csv('/shared-data/out.csv', index=False, mode='w')
        else:
            logging.info("No threats detected")
    except Exception as e:
        print("Error while trying to evaluate: " + str(e))

def create_model(dfNormalized):
    # Definir el autoencoder
    input_size = dfNormalized.shape[1]
    autoencoder = tf.keras.Sequential([
        tf.keras.layers.Dense(input_size, activation='relu'),
        tf.keras.layers.Dense(34, activation='relu'),
        tf.keras.layers.Dense(17, activation='relu'),
        tf.keras.layers.Dense(10, activation='relu'),
        tf.keras.layers.Dense(17, activation='relu'),
        tf.keras.layers.Dense(34, activation='relu'),
        tf.keras.layers.Dense(input_size, activation='sigmoid')
    ])
    
    # Compilar el modelo
    autoencoder.compile(optimizer=tf.keras.optimizers.Adam(),
                        loss=tf.keras.losses.MeanSquaredError())
    
    autoencoder.fit(dfNormalized, dfNormalized, epochs=10, batch_size=16)
    return autoencoder
       
def add_noise_to_weights(model, noise_multiplier):
    for layer in model.layers:
        for param in layer.trainable_weights:
            param.assign_add(tf.random.normal(tf.shape(param), stddev=noise_multiplier))

def train_DP_model(model, X, num_epochs=10, noise_multiplier=0.1):
    for epoch in range(num_epochs):
        add_noise_to_weights(model, noise_multiplier)

    return model   


    