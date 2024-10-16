from core import Core
from dto.website_detail import WebsiteDetails


class Service:
    def __init__(self):
        self.core = Core()

    def extract_documents(self, files, website_details_dto: WebsiteDetails):
        """
        Function sends the files and website urls to the core component where all the processing and extraction takes place.
        :param files:
        :param website_details_dto:
        :return:
        """
        # await asyncio.sleep(1)
        print("Extraction of documents started")
        return self.core.extract_documents(files, website_details_dto)

    def chat_with_knowledge_base(self, question):
        """
        Function sends the questions to the core component where all the handling takes place.
        :param question:
        :return: streaming response from LLM.
        """
        return self.core.chat_with_history(question)
