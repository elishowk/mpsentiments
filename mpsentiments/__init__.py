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
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__="elishowk"
__date__ ="$24 févr. 2011 12:23:02$"

import codecs
from os.path import join

import mpdata
import mpclassify
import mptokenize
import nltk


import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s %(message)s")


def articles_gen(config, dbconnect):
    content_gen = dbconnect.get_contents()
    total=0
    try:
        while 1:
            alltokens = []
            (id, contents) = content_gen.next()
            # tokenizes all selected fields from DB
            for field in contents:
                alltokens += mptokenize.tokenize( nltk.clean_html(field) )
            yield (id, alltokens)
            total+=1
    except StopIteration:
        logging.debug( "analyzed %d articles"%total )

def export_chart(config):
    db = mpdata.Database(config)
    db.export_results()

def main(config):
    classifier = mpclassify.train_classifier(config)
    dbconnect = mpdata.Database(config)
    articletokens_gen = articles_gen(config, dbconnect)
    #import pdb
    #pdb.set_trace()
    logging.debug("start classifying input data set")
    #results = []
    try:
        while 1:
            (id, tokens) = articletokens_gen.next()
            predict_class = classifier.classify( mpclassify.word_feats(tokens) )
            #logging.debug(predict_class)
            #results += [(id, predict_class)]
            dbconnect.write_class((id, predict_class))
            #results.write( '"%s","%s"\n'%( predict_class, " ".join(tokens) ) )
    except StopIteration:
        #results.close()
        #dbconnect.write_class(results)
        return