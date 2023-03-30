'''
Created on 30.03.2023

@author: wf
'''
import dataclasses

class DataClassUtil:
    """
    https://gist.github.com/gatopeich/1efd3e1e4269e1e98fae9983bb914f22
    
    https://stackoverflow.com/a/54769644/1497139
    """

    @classmethod
    def dataclass_from_dict(cls,klass, d):
        try:
            fieldtypes = {f.name:f.type for f in dataclasses.fields(klass)}
            return klass(**{f:cls.dataclass_from_dict(fieldtypes[f],d[f]) for f in d})
        except:
            return d # Not a dataclass field
