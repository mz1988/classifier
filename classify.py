#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
__author__ = "Morteza Zandieh"
__license__ = "MIT"
"""

import codecs, math
import operator
import fermat.classifiers.nb as nb
import fermat.classifiers.nb
from fermat  import preprocessing
from config import class_map, geo_main_class_map

stopwords = set()
f = codecs.open(pre_path + '/fermat/data/stopwords', 'r')
for s in f:
    stopwords.add(preprocessing.safeunicode(s[:-1]))
f.close()

f = codecs.open(pre_path + '/fermat/data/verbs', 'r')
for s in f:
    stopwords.add(preprocessing.safeunicode(s[:-1]))
f.close()

def classify(text):
    """classify your document - contexual tags @config file
    """    
    rdh = nb.NBRedisDataHandler(db=1)
    n = nb.NaiveBayes(rdh)
    newstest = nb.preprocessing.safeunicode(text)
    scores = n.classify(nb.extract_words(text, stopwords))
    scores = sorted(scores.iteritems(), key=operator.itemgetter(1))
    
    #find topic tag
    for i in scores:
        if i[0].find('t_') == 0:
            topic_tag = i[0]
    
    #find main geo tag
    for i in scores:
        if i[0].find('geotagm_') == 0:
            geom_tag = i[0]
            geom_tag = geo_main_class_map[str(geom_tag)] 


    return {'topic':class_map[str(topic_tag)],
            'geo_tag': geom_tag
            }
    
    
def train(cat, text):
    """train your document - as text and category
    tags can be anything
    """    
    rdh = nb.NBRedisDataHandler(db=1)
    n = nb.NaiveBayes(rdh)
    newstest = preprocessing.safeunicode(text)
    train = n.train(cat, nb.extract_words(newstest, stopwords))
        
    return "@" +  str(cat) + " trained"
    

