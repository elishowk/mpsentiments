# -*- coding: utf-8 -*-
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/gpl.html>.

from nltk.classify import NaiveBayesClassifier
from os.path import exists, join
import cPickle

import mpdata
import mptokenize

import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s %(message)s")

def word_feats(words):
    """
    Common method constructing the feature set
    """
    return dict([("contains-word(%s)"%word, True) for word in words])

def process_meanrating(config):
    sourcetype = config['training']['type']
    path = join( config['data_path'], config['training']['path'] )
    dataclass = _dynamic_get_class("mpdata", sourcetype)
    data = dataclass( path,  dialect="excel")
    for com in data:
        # skip first line
        break
    # training
    mean = data.getMeanRating()
    logging.debug("total of bad lines : %d"%data.impossible_line)
    cPickle.dump(mean, open(config['ratingsmean'], 'w+b'))
    return mean

def get_ratingsmean(config):
    logging.debug("getting rating mean or fixed value")
    if 'fixedrating' not in config:
        if not exists(config['ratingsmean']):
            return process_meanrating(config)
        else:
            return cPickle.load(open(config['ratingsmean'], 'rb'))
    else:
        return config['fixedrating']

def features_gen(config):
    """
    Reads the training data set and yields feature sets associated with class labels
    """
    ratingsmean = get_ratingsmean(config)
    logging.debug("middle rating value used for training = %d"%ratingsmean)
    sourcetype = config['training']['type']
    path = join( config['data_path'], config['training']['path'] )
    dataclass = _dynamic_get_class("mpdata", sourcetype)
    data = dataclass( path,  dialect="excel")
    for com in data:
        if 'rating' in com:
            if com['rating'] >= ratingsmean:
                yield (word_feats(mptokenize.tokenize(com['body'])), 'pos')
            else:
                yield (word_feats(mptokenize.tokenize(com['body'])), 'neg')
    logging.debug("total of bad lines : %d"%data.impossible_line)

def train_classifier(config):
    """
    Trains a NaiveBayesClassifier on input data if not already pickled
    """
    if not exists(config['classifier']):
        logging.debug("training a new classifier")
        trainfeats = []
        features = features_gen(config)
        try:
            while 1:
                trainfeats += [features.next()]
        except StopIteration:
            classifier = NaiveBayesClassifier.train(trainfeats)
            cPickle.dump(classifier, open(config['classifier'], 'w+b'))
    else:
        logging.debug("using existing classifier at %s"%config['classifier'])
        classifier = cPickle.load(open(config['classifier'], 'rb'))

    return classifier

def _dynamic_get_class(mod_name, class_name):
    """returns a class given its name"""
    mod = __import__(mod_name, globals(), locals(), [class_name])
    return getattr(mod, class_name)
