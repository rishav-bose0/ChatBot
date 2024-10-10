import os
from langchain_openai import ChatOpenAI


class GptLLM:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini")

    def get_llm(self):
        return self.llm



