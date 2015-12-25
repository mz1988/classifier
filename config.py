"""
__author__ = "Morteza Zandieh"
__license__ = "MIT"
"""

pre_path = '/Users/Morteza/Life/classifier'

Config = {
    'pre_path': pre_path,
    
    'service_ip':'127.0.0.1:8086',
    
    'mongo': {
        'name':'sun',
        'host':'localhost',
        'port':27017
    },
    'redis': {
        'host':'localhost'
    }
}

class_map = {'t_Politics':u'سیاسی','t_Economics':u'اقتصادی', 't_Sports':u'ورزشی', 
                 't_Art-Cultural-Enter.':u'فرهنگی', 't_Social':u'اجتماعی', 
                 't_Sci-Tech':u'دانش و فناوری'}

geo_main_class_map = {'geotagm_Iran':u'ایران','geotagm_World':u'بین الملل'}
 