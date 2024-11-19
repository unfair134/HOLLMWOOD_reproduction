from langchain_openai import ChatOpenAI
from langchain_community.callbacks.manager import get_openai_callback
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from .BaseLLM import BaseLLM

import os

class LangChainGPT(BaseLLM):

    def __init__(self, model="gpt-3.5-turbo"):
        super(LangChainGPT, self).__init__()
        self.model_name = model
        if "OPENAI_API_BASE" in os.environ:
            from dotenv import load_dotenv
            load_dotenv()
            api_base = os.environ["OPENAI_API_BASE"]
            api_key = os.environ["OPENAI_API_KEY"]
            self.chat_model = ChatOpenAI(model=self.model_name, openai_api_base=api_base)
        else:
            api_key = os.environ.get("OPENAI_API_KEY", None)

            if api_key is None:
                print("warning! call LangChainGPT but openai key has not yet been set, use idle key instead")
                os.environ["OPENAI_API_KEY"] = "not_a_key"

            self.chat_model = ChatOpenAI(model=self.model_name)
                
        # add api_base        
        self.messages = []

    def initialize_message(self):
        self.messages = []

    def ai_message(self, payload):
        self.messages.append(AIMessage(content=payload))

    def system_message(self, payload):
        self.messages.append(SystemMessage(content=payload))

    def user_message(self, payload):
        self.messages.append(HumanMessage(content=payload))

    def get_response(self):
    
        with get_openai_callback() as cb:        
            response = self.chat_model.invoke(self.messages)
        total_tokens = cb.total_tokens
        return response.content
    
    def chat(self,text):
        self.initialize_message()
        self.user_message(text)
        response = self.get_response()
        return response
    
    def print_prompt(self):
        for message in self.messages:
            print(message)
