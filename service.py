from core import Core


class Service:
    def __init__(self):
        self.core = Core()

    def extract_documents(self):
        # documents = ["data/tata-motor-report.pdf", "data/mahindra_report.pdf"]
        documents = ["data/tata-motor-report.pdf"]
        return self.core.extract_documents(documents)

    def chat_with_knowledge_base(self, question):
        # return self.core.chat_with_knowledge_base(question)
        return self.core.chat_with_history(question)
