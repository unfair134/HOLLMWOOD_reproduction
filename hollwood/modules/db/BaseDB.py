# BaseDB.py

from abc import ABC, abstractmethod

class BaseDB(ABC):
    
    @abstractmethod
    def init_from_data(self, data):
        pass
    @abstractmethod
    def save(self, file_path):
        pass

    @abstractmethod
    def load(self, file_path):
        pass

    @abstractmethod
    def search(self, query, n_results):
        pass

 

    