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
import utils
import loadProcData

class ClientNFStream(fl.client.NumPyClient):
    def __init__(self, model):
        self.model = model
        self.threshold = 0.5
                
    def get_parameters(self, config):
        utils.logging.info("GET PARAMITERS:")
        return self.model.get_weights()
        
    def fit(self, parameters, config):
        utils.logging.info("FIT:")
        dfNormalized, _ = loadProcData.load_and_preprocess_data()
        utils.logging.info("rec:")
        self.model.set_weights(parameters)
        utils.logging.info("setting weights")
        self.model.fit(dfNormalized, dfNormalized, epochs=1, batch_size=32)
        loss, accuracy = self.model.evaluate(dfNormalized, dfNormalized)
        utils.logging.info("returing params to the server")
        return self.model.get_weights(), len(dfNormalized), {"accuracy": accuracy}

    def evaluate(self, parameters, config):
        utils.logging.info("EVALUATE:")
        dfNormalized, _ = loadProcData.load_and_preprocess_data()
        self.model.set_weights(parameters)
        utils.logging.info("setting weights")
        loss, accuracy = self.model.evaluate(dfNormalized, dfNormalized)
        utils.logging.info("returning params to the server")
        reconstructions = self.autoencoder.predict(dfNormalized)
        train_loss = tf.keras.losses.mae(reconstructions, dfNormalized)
        self.threshold = np.mean(train_loss) + 2*(np.std(train_loss))
        return loss, len(dfNormalized), {"accuracy": accuracy}

class ClientZKP(fl.client.NumPyClient):
    def __init__(self, model):
        self.model = model
        self.threshold = 0.5

    def get_parameters(self, config):
        utils.logging.info("GET PARAMITERS:")
        return self.model.get_weights()
        
    def fit(self, parameters, config):
        utils.logging.info("FIT:")
        dfNormalized, _ = loadProcData.load_and_preprocess_data()
        utils.logging.info("rec:")
        self.model.set_weights(parameters)
        utils.logging.info("setting weights")
        self.model.fit(dfNormalized, dfNormalized, epochs=1, batch_size=32)
        loss, accuracy = self.model.evaluate(dfNormalized, dfNormalized)
        utils.logging.info("returing params to the server")
        return self.model.get_weights(), len(dfNormalized), {"accuracy": accuracy}

    def evaluate(self, parameters, config):
        utils.logging.info("EVALUATE:")
        dfNormalized, _ = loadProcData.load_and_preprocess_data()
        self.model.set_weights(parameters)
        utils.logging.info("setting weights")
        loss, accuracy = self.model.evaluate(dfNormalized, dfNormalized)
        utils.logging.info("returning params to the server")
        reconstructions = self.autoencoder.predict(dfNormalized)
        train_loss = tf.keras.losses.mae(reconstructions, dfNormalized)
        self.threshold = np.mean(train_loss) + 2*(np.std(train_loss))
        return loss, len(dfNormalized), {"accuracy": accuracy}
           
class ClientZKPAndDP(fl.client.NumPyClient):
    def __init__(self, model):
        self.model = model
        self.threshold = 0.5

    def get_parameters(self, config):
        utils.logging.info("GET PARAMITERS:")
        return self.model.get_weights()
        
    def fit(self, parameters, config):
        utils.logging.info("FIT:")
        dfNormalized, _ = loadProcData.load_and_preprocess_data()
        utils.logging.info("rec:")
        self.model.set_weights(parameters)
        utils.logging.info("setting weights")
        #utils.logging.info(parameters)
        self.model.fit(dfNormalized, dfNormalized, epochs=1, batch_size=32)
        utils.logging.info("adding noise to the weights...")
        #add DP
        utils.train_DP_model(self.model, dfNormalized, 10, 0.1) 
        utils.logging.info("evaluate...")
        loss, accuracy = self.model.evaluate(dfNormalized, dfNormalized)
        utils.logging.info("returing params to the server")
        return self.model.get_weights(), len(dfNormalized), {"accuracy": accuracy}

    def evaluate(self, parameters, config):
        utils.logging.info("EVALUATE:")
        dfNormalized, _ = loadProcData.load_and_preprocess_data()
        self.model.set_weights(parameters)
        utils.logging.info("setting weights")
        loss, accuracy = self.model.evaluate(dfNormalized, dfNormalized)
        utils.logging.info("returning params to the server")
        reconstructions = self.autoencoder.predict(dfNormalized)
        train_loss = tf.keras.losses.mae(reconstructions, dfNormalized)
        self.threshold = np.mean(train_loss) + 2*(np.std(train_loss))        
        return loss, len(dfNormalized), {"accuracy": accuracy}


class ClientDP(fl.client.NumPyClient):
    def __init__(self, model):
        self.model = model
        self.threshold = 0.5 
        
    def get_parameters(self, config):
        return self.model.get_weights()

    def fit(self, parameters, config):
        self.model.set_weights(parameters)
        utils.logging.info("set weights")
        dfNormalized, _ = loadProcData.load_and_preprocess_data()
        utils.logging.info("load data")
        self.model.fit(dfNormalized, dfNormalized, epochs=10, batch_size=16, validation_split=0.2, shuffle=True)
        utils.train_DP_model(self.model, dfNormalized, 10, 0.1) 
        return self.model.get_weights(), len(dfNormalized), {}

    def evaluate(self, parameters, config):
        self.model.set_weights(parameters)
        _, dfNormalizedTest = loadProcData.load_and_preprocess_data()
        loss = self.model.evaluate(dfNormalizedTest, dfNormalizedTest)
        reconstructions = self.autoencoder.predict(dfNormalizedTest)
        train_loss = tf.keras.losses.mae(reconstructions, dfNormalizedTest)
        self.threshold = np.mean(train_loss) + 2*(np.std(train_loss))        
        return loss, len(dfNormalizedTest), {}
