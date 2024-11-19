import chromadb
from .BaseDB import BaseDB
import random
import string
import os

class ChromaDB(BaseDB):
    
    def __init__(self,embedding):
        self.collection = None
        self.embedding = embedding

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.path = os.path.join(base_dir, "./chromadb_saves/")
        self.client = chromadb.PersistentClient(path = self.path)

    def init_from_data(self, data, db_name):
        if db_name in [c.name for c in self.client.list_collections()]:
            self.collection = self.client.get_collection(name=db_name,embedding_function=self.embedding)
        else:
            self.collection = self.client.create_collection(name=db_name,embedding_function=self.embedding)
            if len(data) != 0:
                self.collection.add(
                    documents=data,
                    ids=[str(i) for i in  list(range(len(data)))]
                )
        return 
    
    def save(self, file_path):
        if file_path != self.path:
            # copy all files in self.path to file_path, with overwrite
            os.system("cp -r " + self.path + " " + file_path)
            previous_path = self.path
            self.path = file_path
            self.client = chromadb.PersistentClient(path = file_path)
            # remove previous path if it start with tempdb
            if previous_path.startswith("tempdb"):
                os.system("rm -rf " + previous_path)
                        

    def load(self, file_path):
        self.path = file_path
        self.client = chromadb.PersistentClient(path = file_path)
        self.collection = self.client.get_collection("search")

    def search(self, query, n_results):
        results = self.collection.query(query_texts=[query], n_results=n_results)
        return results['documents'][0]

    def init_from_docs(self, vectors, documents):
        if self.client is None:
            self.init_db()
        
        ids = []
        for i, doc in enumerate(documents):
            first_four_chat = doc[:min(4, len(doc))]
            ids.append( str(i) + "_" + doc)
        self.collection.add(embeddings=vectors, documents=documents, ids = ids)
        
