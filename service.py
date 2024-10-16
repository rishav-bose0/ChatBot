from core import Core
from dto.website_detail import WebsiteDetails


class Service:
    def __init__(self):
        self.core = Core()

    def extract_documents(self, files, website_details_dto: WebsiteDetails):
        # documents = ["data/tata-motor-report.pdf", "data/mahindra_report.pdf"]
        # documents = ["data/tata-motor-report.pdf"]
        return self.core.extract_documents(files, website_details_dto)

    def chat_with_knowledge_base(self, question):
        """
        Function sends the questions to the core component where all the handling takes place.
        :param question:
        :return: streaming response from LLM.
        """
        return self.core.chat_with_history(question)
