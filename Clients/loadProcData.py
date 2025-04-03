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

def load_and_preprocess_data(): 
    # Cargar datos desde un archivo CSV y convertirlo en un DataFrame de pandas.
    df = pd.DataFrame(pd.read_csv('/shared-data/out.csv'))
    dfTest = pd.DataFrame(pd.read_csv('./shared-data/out.csv'))

    # Comprobar si la columna 'Label' está presente en el DataFrame
    if 'Label' in df.columns:
        # Dividir características y etiquetas
        X = df.drop(columns=['Label'])
    else:
        # Si la columna 'Label' no está presente, utilizar solo las características X
        X = df

    # Definir las columnas numéricas y categóricas
    numeric_features = X.select_dtypes(include=['float64', 'int64']).columns
    categorical_features = X.select_dtypes(include=['object']).columns

    # Construir un preprocesador para las características numéricas
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler())])

    # Construir un preprocesador para las características categóricas
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))])

    # Combinar preprocesadores para todas las características
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)])

    columns_to_drop = ['id', 'expiration_id', 'src_ip', 'src_mac', 'src_oui', 'src_port', 'dst_ip', 'dst_mac',
                       'dst_oui']
    df.drop(columns=columns_to_drop, inplace=True)
    dfTest.drop(columns=columns_to_drop, inplace=True)

    imputer = SimpleImputer(strategy='mean')
    dfImputed = imputer.fit_transform(df)
    dfTestImputed = imputer.fit_transform(dfTest)

    scaler = MinMaxScaler()
    dfNormalized = scaler.fit_transform(dfImputed)
    dfNormalizedTest = scaler.fit_transform(dfTestImputed)
    return dfNormalized, dfNormalizedTest