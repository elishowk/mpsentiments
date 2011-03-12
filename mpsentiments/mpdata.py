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

import MySQLdb
import codecs
import csv
import json

import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s %(message)s")


class Database(object):
    """
    get all the results with :
    SELECT user_id, title, body, class_label FROM articles AS art JOIN articles_class AS artcl on (art.id=artcl.article_id);
    
    count negs and pos:
    select count(*) from articles_class where class_label='neg';
    select count(*) from articles_class where class_label='pos';
    """
    def __init__(self, config):
        self.config = config
        self.db = MySQLdb.connect(user=config['input']['mysql']['user'],\
            passwd=config['input']['mysql']['password'],\
            db=config['input']['mysql']['database'])

    def get_contents(self):
        columns = ",".join(self.config['input']['mysql']['contents'])
        curs = self.db.cursor()
        curs.execute("SELECT %s FROM %s"%(columns, self.config['input']['mysql']['table']))
        result = curs.fetchone()
        while result is not None:
            id = result[0]
            resultsfiltered = result[1:]
            yield (id, resultsfiltered)
            result = curs.fetchone()

    def write_class(self, resulttuple):
        curs = self.db.cursor()
        curs.execute(
        """INSERT INTO articles_class (article_id, class_label) VALUES (%s, %s)""", resulttuple
        )

    def export_results(self):
        curs = self.db.cursor()
        usersq = """
SELECT id, permalink
FROM users
where permalink != 'NULL';
        """
        curs.execute(usersq)
        users = dict(curs.fetchall())
#        print users
        negative_query ="""
SELECT count(article_id) AS total_positive FROM articles AS art
JOIN articles_class AS artcl on (art.id=artcl.article_id)
where class_label='neg' and user_id=%s;
        """
        positive_query = """
SELECT count(article_id) AS total_positive FROM articles AS art
JOIN articles_class AS artcl on (art.id=artcl.article_id)
where class_label='pos' and user_id=%s;
        """
        jsonresult = []
        for id, permalink in users.iteritems():
            total=0
            user_id = int(id)
            curs.execute(negative_query, (user_id,))
            negativeresult = curs.fetchone()
            total += negativeresult[0]

            curs.execute(positive_query, (user_id,))
            positiveresult = curs.fetchone()
            total +=  positiveresult[0]
            if total>0:
                logging.debug("saving user %s results"%permalink)
                jsonresult += [{'permalink':permalink, 'negatives': negativeresult[0], 'positives': positiveresult[0]}]
            
        jsonout = open( self.config['output'], 'w+b')
        jsonout.write("var data = "+json.dumps(jsonresult)+";\n")
        jsonout.write("var classes = ['negatives','positives'];\n")
        jsonout.close()

class UTF8Recoder(object):
    """
    Iterator that reads an encoded stream and reencodes the input to UTF_8
    """
    def __init__(self, f):
        self.decodedreader = f
        self.utf8encoder = codecs.getencoder("utf_8")

    def __iter__(self):
        return self

    def next(self):
        """
        Encodes next line to utf_8
        """
        encodedline = self.utf8encoder( self.decodedreader.next(), 'ignore' )
        return encodedline[0]

class BaseCsv(object):
    """
    A CSV fieldnames iterator
    handles safe decoding to unicode
    """
    def __init__(self, path, **kwargs):
        # gets columns names
        f1 = self.open( path )
        if f1 is None:
            raise IOError("%s not found"%path)
            return
        tmp = csv.reader( f1, dialect=kwargs['dialect'])
        #tmp = csv.reader( f1, dialect=kwargs['dialect'], quoting=csv.QUOTE_NONNUMERIC )
        self.fieldnames = tmp.next()
        del f1, tmp
        self.reader = self.getReader(path, **kwargs)
        self.reader.next()
        self.line_num = 1
        self.impossible_line = 0

    def getReader(self, path, **kwargs):
        recodedcsvfile = UTF8Recoder(self.open(path))
        return csv.DictReader(
            recodedcsvfile,
            fieldnames=self.fieldnames,
            dialect=kwargs['dialect'],
            restkey="unknown",
            restval="",
            quoting=csv.QUOTE_ALL
        )

    def open(self, path):
        return open(path, 'rU')

    def _utf8_to_unicode(self, row):
        """
        Static utf_8 to unicode decoder
        Dedicated to decode csv.DictReader lines output
        """
        unicoderow = {}
        for k,s in row.iteritems():
            try:
                unicoderow[k] = unicode(s, encoding="utf_8", errors='ignore')
            except Exception, ex:
                _logger.error("basecsv._row_to_unicode(), line %d, reason : %s"%(self.reader.line_num, ex))
        return unicoderow

    def next(self):
        try:
            row = self.reader.next()
        except StopIteration, si:
            raise StopIteration(si)
        except Exception, ex:
            logging.error("csv reading error line %d, reason : %s"%(self.reader.line_num, ex))
            return None
        else:
            return self._utf8_to_unicode(row)

    def __iter__(self):
        return self

class Comments(BaseCsv):
    """
    converts rating to integer
    calculates the means value

    how to clean csv:
    import codecs
    import re

    input = codecs.open("data/comments_with_ratings.csv","r",errors="ignore",encoding="utf-8")
    output = codecs.open("data/comments_with_ratings_clean.csv","w+",errors="ignore",encoding="utf-8")
    reg = re.compile(u"\u2028|\u2029|\u000A|\u000C|\u000D|\u0085",re.I|re.M|re.U)
    for line in input:
        output.write( reg.sub("",line) + "\n" )

    """

    def __init__(self, path, **kwargs):
        BaseCsv.__init__(self, path, **kwargs)
        self.rating_sum = 0
        self.rating_num = 0

    def getReader(self, path, **kwargs):
        return self.open(path)

    def open(self, path):
        return codecs.open(path, 'r', errors='ignore', encoding='utf_8')

    def next(self):
        try:
            row = self.reader.next()
            self.line_num += 1
        except StopIteration, si:
            raise StopIteration(si)
        except Exception, ex:
            logging.error("csv reading error line %d, reason : %s"%(self.reader.line_num, ex))
            return {}
        else:
            row = row.strip(' "\n')
            decoded = row.split('","')
            #print decoded
            if decoded is not None and len(decoded)==2:
                rowdict = {}
                rowdict['rating'] = int(decoded[1])
                rowdict['body'] = decoded[0]
                self.rating_sum += rowdict['rating']
                self.rating_num += 1
                return rowdict
            else:
                self.impossible_line+=1
                #logging.warning("impossible to parse line %d \n %s"%(self.line_num, decoded))
                return {}

    def getMeanRating(self):
        return float(self.rating_sum)/float(self.rating_num)



def usersToDatabase(config):
    """
    Utility importing users csv to database
    """
    input = csv.DictReader(open(config['input']['users'],'rU'),\
        fieldnames=["id","editor","admin","permalink"],\
        dialect=csv.excel_tab)

    db = MySQLdb.connect(user=config['input']['mysql']['user'],\
        passwd=config['input']['mysql']['password'],\
        db=config['input']['mysql']['database'])

    try:
        curs = db.cursor()
        input.next()
        while 1:
            line = input.next()
            print (int(line['id']), int(line['admin']), line['permalink'], int(line['editor']))
            curs.execute(
            """INSERT INTO users (id , admin, permalink, editor) VALUES (%s, %s, %s, %s)""",\
                (int(line['id']), int(line['admin']), line['permalink'], int(line['editor']))
            )
    except StopIteration, si:
        return