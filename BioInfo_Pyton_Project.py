# -*- coding: utf-8 -*-
"""Cleaned_DownloadVer_Project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1m50yFvUs7N-k8ybtbOiH3uucvg1JrLqp

# **Binformatics Machine Learning Project**

Rekkab Gill\
rekkab@uoguelph.ca\
Date April 9 2021\
Dataset: Mice Expression Data from UCI Machine Learning repository\


NOTE: The code here pulls the UCI dataset from google drive, so in order to run the code you must mount your google drive and indicate the location of the dataset or alter the code to use your own way of obtaining the dataset.
"""

# Commented out IPython magic to ensure Python compatibility.
!pip install -q sklearn

# %tensorflow_version 2.x  # this line is not required unless you are in a notebook

from __future__ import absolute_import, division, print_function, unicode_literals

import tensorflow as tf
import io
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from IPython.display import clear_output
from google.colab import files
from tensorflow import keras
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam
from matplotlib import pyplot as plt
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import KFold
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from keras.wrappers.scikit_learn import KerasClassifier
from sklearn import metrics
from sklearn.decomposition import PCA
from google.colab import drive
drive.mount('/content/drive')
# %matplotlib inline
# %config InlineBackend.figure_format='retina'

#put dataset into the dataframe
dataSetAll = pd.read_csv('/content/drive/My Drive/School/UoGuelph/CIS6060 Bioinformatics/Project/the_dataset/mice.csv')
pd.set_option('min_rows',200)
pd.set_option('max_rows',2000)

dataSetAll.isnull().sum() #lets look at the overall count of missing vals

#drop the columns we don't need and those that are missing alot of data
dataSetAll.drop('MouseID',axis=1,inplace=True)
dataSetAll.drop('BAD_N',axis=1,inplace=True)
dataSetAll.drop('BCL2_N',axis=1,inplace=True)
dataSetAll.drop('H3AcK18_N',axis=1,inplace=True)
dataSetAll.drop('pCFOS_N',axis=1,inplace=True)
dataSetAll.drop('EGR1_N',axis=1,inplace=True)
dataSetAll.drop('H3MeK4_N',axis=1,inplace=True)

dataSetAll.isnull().sum() #lets look at the overall count of missing vals

#dorop any empty columns
dataSetAll.dropna(how = 'any', axis = 0, inplace = True); #drop the row that has NA values
print(dataSetAll.shape) #lets look at the shape

dataSetAll.ClassType = pd.Categorical(dataSetAll.ClassType)
dataSetAll['ClassType'] = dataSetAll.ClassType.cat.codes

#Hot Encode whats necssary and get dummy columns that have the encoding for each categorical column
geno_dummies = pd.get_dummies(dataSetAll.Genotype)
treat_dummies = pd.get_dummies(dataSetAll.Treatment)
behav_dummies = pd.get_dummies(dataSetAll.Behavior)

#Now add all the colums together 
dataSetAll = pd.concat([dataSetAll,geno_dummies,treat_dummies,behav_dummies], axis = 1)

#Next remove the old categorical columns because we don't need them 
dataSetAll.drop(['Genotype','Treatment','Behavior'],axis=1,inplace=True)

#We also want to avoid the dummy variable trap so we remove 1 dummy variable from each categorical colum we encoded, to avoid colinearity 
#Note: often libraries will have this built into the functions so you dont have to worry about this but its still good practice and good to understand.
#This is for regression analysis but since we are doing classificaiton, it doesn't really matter but still good to see how to do:
#For p dummy columns per category we want p-1 columns in our dataframe
dataSetAll.drop(['Ts65Dn','Saline','S/C'],axis=1,inplace=True)

print(dataSetAll.head())

dataSetAll.dtypes
print(dataSetAll['ClassType'])

#create the dataset with the columns we need only
#get the output column
dataSet_output = dataSetAll['ClassType']

#get the input data and remove the output colummn
dataSet_input = dataSetAll.drop('ClassType',axis=1)

#change the data to numpy arrays
dataSet_input = pd.DataFrame.to_numpy(dataSet_input)
dataSet_output = pd.DataFrame.to_numpy(dataSet_output)

#normalize the data 
scaler = preprocessing.StandardScaler()
dataSet_input = scaler.fit_transform(dataSet_input)

#apply the PCA technique to reduce dimentionality 

pca = PCA(n_components = 10)
pca.fit(dataSet_input)

print(pca.explained_variance_ratio_)
dataSet_input = pca.transform(dataSet_input)
print(dataSet_input.shape)

"""# NEURAL NETWORK MODEL

**HOW TO DO K-FOLD CROSS VALIDATION FROM SCRATCH**

---
"""

#lets create a useful function for returning model evaluations 
histories = [];
def get_eval(model,inputSetTrain, test_input, outputSetTrain, test_output):
  History = model.fit(inputSetTrain,outputSetTrain,epochs=100, validation_data= (test_input,test_output), verbose = 0,
                    callbacks = [early_stopper])
  histories.append(History.history)

  predictions = model.predict(test_input)
  predictions = np.argmax(predictions,axis=1)
  #print(predictions)
  prediction_accuracy = metrics.accuracy_score(test_output,predictions)
  prediction_precision = metrics.precision_score(test_output, predictions, average="macro")
  prediction_recall = metrics.recall_score(test_output, predictions, average="macro")

  print('accuracy: ',prediction_accuracy)
  print('precision: ',prediction_precision)
  print('recall: ',prediction_recall)

  # Calculate confusion matrix and print it
  cm = metrics.confusion_matrix(test_output, predictions)
  print(cm)
  
  return model.evaluate(test_input, test_output)

#Lets run KFold cross validations

folds = StratifiedKFold(n_splits = 5, shuffle=True,random_state=1)
#folds = KFold(n_splits = 5, shuffle=True,random_state=1)

for train_index, test_index in folds.split(dataSet_input,dataSet_output):
  training_input = dataSet_input[train_index]
  testing_input = dataSet_input[test_index]
  training_output = dataSet_output[train_index]
  testing_output = dataSet_output[test_index]

  model = tf.keras.models.Sequential()

  #the way you read the below is that it initially expects input in the shape you have listed below and then spits out the value to the left, i.e. 128. The activiation indicates what function to use in that layer
  model.add(tf.keras.layers.Dense(7,input_shape=(10,),activation='relu')) #1st hidden layer        
  #model.add(tf.keras.layers.Dense(4, activation='relu')) # 2nd hidden layer (3)
  model.add(tf.keras.layers.Dense(8, activation = 'softmax'))  # output layer (4)


  #compile the model
  model.compile(Adam(learning_rate = 0.001),
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy'])

  #early stopper
  early_stopper = EarlyStopping(monitor = 'val_loss',min_delta = 0.01, patience = 5)

  print(get_eval(model,training_input, testing_input, training_output, testing_output))

"""**HERE WE DO THE SAME AS ABOVE BUT USING THE SKLEARN BUILT IN FUNCTIONALITY**

---


"""

#early stopper function to use for prevent overfitting
early_stopper = EarlyStopping(monitor = 'val_loss',min_delta = 0.01, patience = 5)

def createNetwork():

  model = tf.keras.models.Sequential()

  #the way you read the below is that it initially expects input in the shape you have listed below and then spits out the value to the left, i.e. 128. The activiation indicates what function to use in that layer
  model.add(tf.keras.layers.Dense(7,input_shape=(10,),activation='relu')) #1st hidden layer        
  #model.add(tf.keras.layers.Dense(4, activation='relu')) # 2nd hidden layer (3)
  model.add(tf.keras.layers.Dense(8, activation = 'softmax'))  # output layer (4)


  #compile the model
  model.compile(Adam(learning_rate = 0.001),
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy'])

  return model

nn = KerasClassifier(build_fn = createNetwork, epochs = 100, verbose = 0)
strat_fold= StratifiedKFold(n_splits=10, shuffle=True, random_state= 1) #the strat_fold function is good for making sure the same amount of classes are in each fold so we use that in the corss_val_Score, instead of the default which is just throwing a value in there.
cross_val_score(nn,dataSet_input, dataSet_output, cv = strat_fold)

"""# SUPPORT VECTOR MACHINE MODEL"""

#lets do a grid search for the best parameters
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import GridSearchCV
from sklearn import metrics


parameters = [
        {'C': [1, 10, 100, 1000], 'kernel': ['linear']},
        {'C': [1, 10, 100, 1000], 'kernel': ['rbf'],
                'gamma': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]}]


#split the dataset to get validation
ds_input, validation_input, ds_output, validation_output = train_test_split(dataSet_input, dataSet_output, test_size=0.15, random_state = 1)

#get the best parameters
svm_search = GridSearchCV(SVC(),parameters,n_jobs=-1,verbose=1)
svm_search.fit(validation_input,validation_output)
best_params = svm_search.best_params_

folds = StratifiedKFold(n_splits = 5, shuffle=True,random_state=1)

for train_index, test_index in folds.split(ds_input,ds_output):
  training_input = ds_input[train_index]
  testing_input = ds_input[test_index]
  training_output = ds_output[train_index]
  testing_output = ds_output[test_index]

  svm_model = SVC(**best_params)

  svm_model.fit(training_input,training_output)

  predictions = svm_model.predict(testing_input)

  prediction_accuracy = metrics.accuracy_score(testing_output,predictions)

  prediction_precision = metrics.precision_score(testing_output, predictions, average="macro")
  prediction_recall = metrics.recall_score(testing_output,predictions, average="macro")

  print('accuracy: ',prediction_accuracy)
  print('precision: ',prediction_precision)
  print('recall: ',prediction_recall)

  # Calculate confusion matrix and print it
  cm = metrics.confusion_matrix(testing_output, predictions)
  print(cm)

"""# LOGISTIC REGRESSION MODEL"""

#lets do a grid search for the best parameters

parameters = [
        {'penalty': ['l2'],
         'C': np.logspace(0,4,10),
         'solver': ['lbfgs','newton-cg','liblinear','sag'],
         'max_iter': [5000]
        }]

#split the dataset to get validation
ds_input, validation_input, ds_output, validation_output = train_test_split(dataSet_input, dataSet_output, test_size=0.15, random_state = 1)

#get the best parameters
log_search = GridSearchCV(LogisticRegression(),parameters,n_jobs=-1,verbose=1)
log_search.fit(validation_input,validation_output)
best_params = log_search.best_params_

folds = StratifiedKFold(n_splits = 5, shuffle=True,random_state=1)

for train_index, test_index in folds.split(ds_input,ds_output):
  training_input = ds_input[train_index]
  testing_input = ds_input[test_index]
  training_output = ds_output[train_index]
  testing_output = ds_output[test_index]
  

  log_model = LogisticRegression(**best_params)

  log_model.fit(training_input,training_output)

  predictions = log_model.predict(testing_input)

  prediction_accuracy = metrics.accuracy_score(testing_output,predictions)

  prediction_precision = metrics.precision_score(testing_output,predictions, average="macro")
  prediction_recall = metrics.recall_score(testing_output,predictions, average="macro")

  print('accuracy: ',prediction_accuracy)
  print('precision: ',prediction_precision)
  print('recall: ',prediction_recall)

  # Calculate confusion matrix and print it
  cm = metrics.confusion_matrix(testing_output, predictions)
  print(cm)