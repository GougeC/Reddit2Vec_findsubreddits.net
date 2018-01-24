import pandas as pd
import numpy as np
import nltk
import pymongo
import re
from collections import Counter
import string
from nltk import word_tokenize
import tensorflow as tf
import time
import random
from keras.preprocessing.sequence import pad_sequences
from keras.layers import Embedding, Dense, Reshape, merge
from keras.models import Model
import pickle
import word2vec_preperation_functions as w2vp

if __name__ == '__main__':
    client = pymongo.MongoClient('mongodb://ec2-54-214-228-72.us-west-2.compute.amazonaws.com:27017/')
    db = client.get_database('capstone_db')

    datapoints, sub_labels, word_mapping = w2vp.prepare_for_word2vec(db)
    reverse_dictionary = dict(zip(wm.values(), wm.keys()))
    window_size = 3
    vector_dimension = 300
    epochs = 1000
    validation_size = 16
    validation_window = 100
    validation_examples = np.random.choice(validation_window, validation_size, replace=False)
    vocab_size = 50000

    num_samples = len(datapoints)
    max_length = 100
    word_mapping['NONCE'] = vocab_size+1
    datapoints = pad_sequences(datapoints, maxlen = max_length, dtype = 'int32',
                                     padding = 'post', truncating = 'post', value = vocab_size+1)


    input_datappints = []
    for d in datapoints:
        sampling_table = sequence.make_sampling_table(vocab_size)
        couples, labels = skipgrams(data, vocab_size, window_size=window_size, sampling_table=sampling_table)
        word_target, word_context = zip(*couples)
        word_target = np.array(word_target,dtype = "int32")
        word_context = np.array(word_context,dtype = "int32")
        input_datapoints.append({'word_target':word_target,
                                'word_context':word_context,
                                'labels': labels})


    input_target = keras.Input((1,))
    input_context = keras.Input((1,))
    embedding = Embedding(vocab_size,vector_dimension,
                                        input_length =1, name = 'word_embedding')
    target = embedding(input_target)
    target = Reshape((vector_dimension,1))(target)
    context = embedding(input_context)
    context = Reshape((vector_dimension,1))(target)

    dot_product = merge([target, context], mode='dot', dot_axes=1)
    dot_product = Reshape((1,))(dot_product)
    output = Dense(1,activation = 'sigmoid')(dot_product)
    similarity = merge([target, context], mode='cos', dot_axes=0)

    model = Model(input=[input_target, input_context], output=output)
    model.compile(loss='binary_crossentropy', optimizer='adam')

    validation_model = Model(input = [input_target,input_context], output=similarity)

    class SimilarityCallback:
        def run_sim(self):
            for i in range(valid_size):
                validation_word = reverse_dictionary[valid_examples[i]]
                sim = self._get_sim(datapoints[validation_example[j]])
                top_k = 5 #number of nearest to display
                nearest = (-sim).argsort()[1:top_k+1]
                log_str = "Nearest to {}: ".format(validation_word)
                for k in range(top_k):
                    close = reverse_dictionary[nearest[k]]
                    log_str+= "{}, ".format(close)
                print(log_str)
            def _get_sim(v_w_idx):
                sim = np.zeros((vocab_size,))
                v_w = np.zeros((1,))
                t_w = np.zeros((1,))
                for i in range(vocab_size):
                    v_w = v_w_idx
                    t_w = i
                    out = validation_model.predict_on_batch([v_w, t_w])
                    sim[i] = out
                return sim

    sim_cb = SimilarityCallback()
    w_target = np.zeros((1,))
    w_context = np.zeros((1,))
    lbls = np.zeros((1,))
    loops = epochs//num_samples
    cnt = 0
    for i in range(loops+1):
        for s in range(num_samples):
            sample = input_datapoints[s]
            idx = np.random.randint(0,len(sample['lables']))
            w_target[0,] = sample['word_target'][idx]
            w_context[0,] = sample['word_context'][idx]
            lbls[0,] = sample['labels'][idx]
            loss = model.train_on_batch([w_target,w_context],lbls)
            cnt+=1
            if cnt%100 == 0:
                print("Interation {}, loss = {}".format(cnt,loss))
            if cnt%1000 == 0:
                sim_sib.run_sim()

    featurized = model.layers[0].get_weights()
    print(featurized.shape)
    np.save('vectorized_words.npy',featurized)
    with open('wordmapping.pkl','wb') as f:
        pickle.dump(word_mapping,f)
    with open('vector_words.pkl','wb')as f:
        pickle.dump(featurized,f)


    def get_featurized_word(word,word_map,feature_mat):
        if word in word_map:
            return feature_map[word_map[word],:]
        else:
            return feature_map[word_map['UNK'],:]
    def get_features_from_num(num,reverse_dictionary,feature_mat):
        if num in reverse_dictionary:
            return feature_mat[num,:]
        else:
            return feature_mat[0,:]

    X = []
    for point in datapoints:
        x_point = []
        for num in datapoints:
            x_point.append(get_features_from_num(num,reverse_dictionary,featurized))
        x_point = np.array(x_point)
        x_point = np.mean(x_point,axis = 0)
        X.append(x_point)
    Xdf = pd.DataFrame(X)
    ydf = pd.Series(sub_labels)
    training_data = Xdf
    training_data['labels'] = ydf
    training_data.to_csv('training_data.csv',index = False)