"""
__author__ = "Morteza Zandieh"
__license__ = "MIT"
"""
from redis import Redis
import urllib
from fermat import preprocessing
import json
import codecs
import itertools, math

class NBDataHandler(object):
    """Default NB Data Handler which used by NaiveBayes for providing needed
       data functions.
       
       This class uses internal python dictionaries and sets.
       
       It can subclassed for supporting other databases.
    """
    def __init__(self):
        # Frequenct of a term in a cat - {cat1:{terms:freq,...},...}
        self.catsfreq = {}
        # Sum of all terms frequency - {cat1:123213, ...}
        self.catsfreq_all = {}
        # Vocublary
        self.voc = set()
        # Number of documents in cat - {cat1:12312, ...}
        self.catsn = {} 
        # number of all docs |D|
        self.n = 0
    
    def incrTermsFreqInCat(self, cat, terms):
        """Increases a term frequency in specified category.

           Terms should be list of tuples. E.g [('term', n), ...]
        """
        if cat not in self.catsfreq:
            self.catsfreq[cat] = {}
            
        catfreq = self.catsfreq[cat]
        catfreqall = self.catsfreq_all
        voc = self.voc
        for t, n in terms:
            voc.add(t)
            catfreqall[cat] = catfreqall.get(cat, 0) + n
            catfreq[t] = catfreq.get(t, 0) + n
        
    
    def incrCountDocsInCat(self, cat, by=1):
        """Increases number of docs in specified category.
        """
        self.n += by
        self.catsn[cat] = self.catsn.get(cat, 0) + by
    
    def termFreqInCat(self, cat, term):
        """Returns frequency of a term in specified category.
        """
        return self.catsfreq[cat].get(term, 0)
    
    def termsFreqInCat(self, cat):
        """Returns sum of all terms frequency is specified category.
        """
        return self.catsfreq_all.get(cat, 0)
    
    def termExists(self, term):
        """Return False if specified term is not existed in vocublary.
        """
        return term in self.voc
    
    def countTerms(self):
        """Returns number of terms.
        """
        return len(self.voc)
    
    def countDocs(self):
        """Returns number of docs.
        """
        return self.n

    def countDocsInCat(self, cat):
        """Returns number of docs in specifed cat.
        """
        return self.catsn.get(cat, 0)
    
    def cats(self):
        """Returns categories.
        """
        return self.catsn.keys()[:]

class NBRedisDataHandler(NBDataHandler):
    def __init__(self, host='localhost', db=0, password=None, prefix='NB'):
        self._host = host
        self._prefix = prefix
        self._dbn = db
        self._password = password
        self._redis = None
        
        self._cache_cats = set()
        
        # Cats
        # #PREFIX#:cats, set(#cats)
                
        # Term in Cat frequency
        # #PREFIX#:#cat:#term, #freq
        
        # Sum of all frequencies in cats
        # #PREFIX#:#cat, #freq
        
        # Vocublary
    
    def dropData(self):
        self._db().flushall()
    
    @staticmethod
    def tosafestr(s):
        """Uses for binarysafe keys.
        """
        return urllib.quote(preprocessing.safestr(s))
    
    @staticmethod
    def fromsafestr(s):
        """Uses for converting binarysafe to unicode.
        """
        return preprocessing.safeunicode(urllib.unquote(s))
        
    def _db(self):
        if self._redis != None:
            try:
                self._redis.ping()
                return self._redis
            except:
                pass
        self._redis = Redis(self._host, db=self._dbn, password=self._password)
        return self._redis
    
    def xaddcat(self, cat):
        safecat = self.tosafestr(cat)
        if cat not in self._cache_cats:
            db = self._db()
            db.sadd('%s:cats'%self._prefix, safecat)
            self.cats()

    # XXX Design a buffer for [some] amount of data
    def incrTermsFreqInCat(self, cat, terms):
        self.xaddcat(cat)
        db = self._db()
        
        safecat = self.tosafestr(cat)
        
        catfreq_key = '%s:catterm:%s:'%(self._prefix, safecat)
        catfreqall_key = '%s:catfreqall:%s'%(self._prefix, safecat)
        voc_key = '%s:voc:'%(self._prefix)
        voc_count_key = '%s:voc_count'%(self._prefix)
        
        for t, n in terms:
            safeterm = self.tosafestr(t)
            
            db.incr(catfreq_key + safeterm, n)
            db.incr(catfreqall_key, n)
            
            # voc, voc_count
            if not db.exists(voc_key + safeterm):
                db.incr(voc_count_key)
            db.incr(voc_key + safeterm, n)
    
    def incrCountDocsInCat(self, cat, by=1):
        self.xaddcat(cat)
        db = self._db()
        
        safecat = self.tosafestr(cat)
        
        n_key = '%s:n'%self._prefix
        catsn_key = '%s:catn:%s'%(self._prefix, safecat)
        
        db.incr(n_key, by)
        db.incr(catsn_key, by)
    
    def termFreqInCat(self, cat, term):
        safeterm = self.tosafestr(term)
        safecat = self.tosafestr(cat)
        db = self._db()
        key = '%s:catterm:%s:%s'%(self._prefix, safecat, safeterm)
        
        n = db.get(key)
        if n != None:
            return int(n)
        return 0
    
    def termsFreqInCat(self, cat):
        safecat = self.tosafestr(cat)
        db = self._db()
        key = '%s:catfreqall:%s'%(self._prefix, safecat)
        
        n = db.get(key)
        if n != None:
            return int(n)
        return 0
    
    def termExists(self, term):
        db = self._db()
        voc_key = '%s:voc:'%(self._prefix)
        safeterm = self.tosafestr(term)
        return db.exists(voc_key + safeterm)
        
    
    def countTerms(self):
        db = self._db()
        key = '%s:voc_count'%(self._prefix)
        
        n = db.get(key)
        if n != None:
            return int(n)
        return 0
    
    def countDocs(self):
        db = self._db()
        key = '%s:n'%self._prefix
        
        n = db.get(key)
        if n != None:
            return int(n)
        return 0

    def countDocsInCat(self, cat):
        safecat = self.tosafestr(cat)
        key = '%s:catn:%s'%(self._prefix, safecat)
        db = self._db()
        
        n = db.get(key)
        if n != None:
            return int(n)
        return 0
    
    def cats(self):
        db = self._db()
        self._cache_cats = \
            set(map(self.fromsafestr, list(db.smembers('%s:cats'%self._prefix))))
        return set(self._cache_cats)

class NaiveBayes(object):
    """Naive Bayes classifier.
    """
    # Prior Nc/n ==> May computed in classify
    
    def __init__(self, datahandler=None):
        if datahandler == None:
            datahandler = NBDataHandler()
        
        self._dh = datahandler
       
    def train(self, cat, docterms):
        """Train docs by specefied cat.
        """
        self._dh.incrCountDocsInCat(cat)
        self._dh.incrTermsFreqInCat(cat, docterms.items())
    
    
    def classify(self, docterms, floatlog=True):
        """Returns result of classifying docs.
        """
        if floatlog:
            log = math.log
        else:
            log = lambda x: x
        
        score = {}
        for c in self._dh.cats():
            score[c] = log(float(self._dh.countDocsInCat(c)) / self._dh.countDocs())
            denom = float(self._dh.termsFreqInCat(c) + self._dh.countTerms())
            for t, f in docterms.items():
                if not self._dh.termExists(t):
                    continue
                num = float(self._dh.termFreqInCat(c, t)) + 1
                if floatlog:
                    score[c] += log((num / denom)) * f
                else:
                    score[c] *= (num / denom) ** f
                               
        return score

def extract_words(text, stopwords = None):
    if stopwords == None:
        stopwords = set()
    x = preprocessing.normalize(preprocessing.safeunicode(text))
    words = preprocessing.remove_puncts(x.replace(preprocessing.HALF_SPACE, ' ')).split(' ')
    words = map(lambda w: w.strip(), words)
    words = preprocessing.gen_ngrams(filter(lambda w: w != '' and w not in stopwords, words), 1)
    words = {i[0][0]:i[1] for i in words.items()}
    return words