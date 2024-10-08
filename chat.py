import os
from langchain_openai import ChatOpenAI


class GptLLM:
    def __init__(self):
        self.api_key = "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"
        self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=self.api_key)

    def get_llm(self):
        return self.llm



