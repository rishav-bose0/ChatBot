import time
from typing import List

from bs4 import BeautifulSoup
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import WebBaseLoader, RecursiveUrlLoader
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.chains import create_history_aware_retriever, create_retrieval_chain

from batch_process import BatchProcess
from constants import prompts, constants
from chat import GptLLM
from dto.website_detail import WebsiteDetails
from file_process import FileUtils
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma


class Core:
    def __init__(self):
        self.vectorstore = None
        self.prompt = hub.pull("rlm/rag-prompt")
        self.file_utils = FileUtils()
        self.embedder = OpenAIEmbeddings()
        self.llm = GptLLM().get_llm()
        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base", chunk_size=256, chunk_overlap=0
        )
        self.ragchain = None
        self.store = {}

    def extract_documents(self, files, website_details_dto: WebsiteDetails):
        """
        Function extracts info from documents and the extracted info is saved to vector store.
        :param files:
        :param website_details_dto:
        :return:
        """
        # First check file type here. if pdf/ weblink / docs etc.
        for file in files:
            extension_name = file.split(".")
            extension_name = extension_name[len(extension_name) - 1]
            if extension_name == "pdf":
                extracted_info = self._extract_pdf_documents(file)
                self._add_texts_to_vectorstore(extracted_info)
            elif extension_name == "docx":
                pass

        if len(website_details_dto.websites) != 0:
            extracted_info = self._extract_website_content(website_details_dto)
            # Threshold of 100. If document list gt 100, store in batches.
            if len(extracted_info) > 100:
                self._process_in_batches(docs_token=extracted_info)
            else:
                self._add_docs_to_vectorstore(docs_token=extracted_info)

    def _extract_text_from_html(self, html_content):
        """
        Function to parse html content and add only texts.
        :param html_content:
        :return:
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for element in soup(['script', 'style']):
            element.decompose()

        # Get text and clean it
        text = soup.get_text(separator='\n', strip=True)
        return text

    def _extract_website_content(self, website_details_dto: WebsiteDetails):
        """
        Function extracts website contents and returns the documents after splitting.
        :param website_details_dto:
        :return:
        """
        for url in website_details_dto.websites:
            if website_details_dto.is_recursive:
                loader = RecursiveUrlLoader(url, extractor=self._extract_text_from_html)
            else:
                loader = WebBaseLoader(url)

            documents = loader.load()

            if len(documents[0].page_content.strip(" ")) == 0:
                # TODO We need to use selenium for extraction.
                # return error that current website cannot be loaded using WebBaseLoader
                pass

            # joined_texts = "\n\n".join(tables)
            docs_token = self.text_splitter.split_documents(documents)
            return docs_token

    def _extract_pdf_documents(self, file_path) -> List[str]:
        """
        PDF docs info are extracted and the text split is returned.
        :param file_path:
        :return:
        """
        raw_pdf_elements = self.file_utils.extract_pdf_elements(file_path)
        texts = self.file_utils.categorize_elements(raw_pdf_elements)

        joined_texts = "\n".join(texts)
        texts_4k_token = self.text_splitter.split_text(joined_texts)
        return texts_4k_token

    def _add_texts_to_vectorstore(self, token_text):
        """
        Function adds text data to vectorstore.
        :param token_text:
        :return:
        """
        if self.vectorstore is None:
            print("Adding to vector store for the first time")
            self.vectorstore = Chroma.from_texts(token_text, embedding=self.embedder, persist_directory="dbstore")
            return
        self.vectorstore.add_texts(texts=token_text)

    def _add_docs_to_vectorstore(self, docs_token):
        """
        Function adds documents info to vectorstore
        :param docs_token:
        :return:
        """
        if self.vectorstore is None:
            print("Adding to vector store for the first time")
            self.vectorstore = Chroma.from_documents(docs_token, embedding=self.embedder, persist_directory="dbstore")
            return

        self.vectorstore.add_documents(docs_token)

    def _get_retriever(self):
        """
        Function initialises the vectorstore with the retriever if vectorstore is not initialised. Else returns the retriever.
        :return:
        """
        if self.vectorstore is None:
            self.vectorstore = Chroma(persist_directory="dbstore", embedding_function=self.embedder)

        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 20})
        return retriever

    def _create_rag_chain(self):
        """
        Function creates a basic ragchain for retrieval of documents, passing to prompt and then to LLM.
        :return:
        """
        retriever = self._get_retriever()
        self.rag_chain = (
                {"context": retriever | self.file_utils.format_docs, "question": RunnablePassthrough()}
                | self.prompt
                | self.llm
                | StrOutputParser()
        )

    def chat_with_knowledge_base(self, question):
        """
        Function uses retrievers and langchain to understand the question, retrieve relevant documents and pass the
        information to LLM to return the response.
        :param question:
        :return:
        """
        self._create_rag_chain()
        for chunk in self.rag_chain.stream(question):
            yield chunk

    def get_session_history(self, session_id) -> BaseChatMessageHistory:
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def chat_with_history(self, question):
        """
        Function uses retrievers and langchain to understand the question, retrieve relevant documents and pass the
        information to LLM to return the response. It tries to understand the question wrt the conversation history.
        :param question:
        :return: streaming response from LLM.
        """

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                (constants.SYSTEM_MESSAGE, prompts.CONTEXTUALISE_QUESTION_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                (constants.HUMAN_MESSAGE, "{input}"),
            ]
        )
        history_aware_retriever_chain = create_history_aware_retriever(
            self.llm, self._get_retriever(), contextualize_q_prompt
        )

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                (constants.SYSTEM_MESSAGE, prompts.QA_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                (constants.HUMAN_MESSAGE, "{input}"),
            ]
        )

        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever_chain, question_answer_chain)

        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

        for chunk in conversational_rag_chain.stream({"input": question},
                                                     config={"configurable": {"session_id": "abc123"}}):
            yield chunk.get('answer', "")

    def embed_and_store(self, docs_batch):
        """
        Add documents in chunks to vectorstore.
        :param docs_batch:
        :return:
        """
        try:
            self._add_docs_to_vectorstore(docs_token=docs_batch)
        except Exception as e:
            print(f"Error embedding batch: {e}")
            time.sleep(4)  # Wait before retrying
            self.embed_and_store(docs_batch)  # Retry

    def _process_in_batches(self, docs_token):
        for batch in BatchProcess().chunk_documents(docs_token, constants.BATCH_SIZE):
            self.embed_and_store(batch)
            time.sleep(1)  # Delay between batches to respect rate limits
