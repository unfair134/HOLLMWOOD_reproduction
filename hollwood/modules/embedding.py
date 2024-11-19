from transformers import AutoModel, AutoTokenizer
from functools import partial
import torch

class EmbeddingModel:
    def __init__(self, model_name, language='en'):
        self.model_name = model_name
        self.language = language
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)

    def __call__(self, input):
        inputs = self.tokenizer(input, return_tensors="pt", padding=True, truncation=True, max_length=256)
        with torch.no_grad():
            outputs = self.model(**inputs)
        embeddings = outputs.last_hidden_state[:, 0, :].tolist()
        return embeddings

class OpenAIEmbedding:
    def __init__(self, model_name="text-embedding-ada-002"):
        from openai import OpenAI
        self.client = OpenAI()
        self.model_name = model_name

    def __call__(self, input):
        if isinstance(input, str):
            input = input.replace("\n", " ")
            return self.client.embeddings.create(input=[input], model=self.model_name).data[0].embedding
        elif isinstance(input,list):
            return [self.client.embeddings.create(input=[sentence.replace("\n", " ")], model=self.model_name).data[0].embedding for sentence in input]

def get_embedding_model(embed_name, language='en'):
    model_name_dict = {
        "bge": "BAAI/bge-large-",
        "luotuo": "silk-road/luotuo-bert-medium",
        "bert": "google-bert/bert-base-multilingual-cased",
    }
    
    if embed_name in model_name_dict:
        model_name = model_name_dict[embed_name]
        if 'bge' in model_name:
            model_name += language
        return EmbeddingModel(model_name)
    else:
        return OpenAIEmbedding()

