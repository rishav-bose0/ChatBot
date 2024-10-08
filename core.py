from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.chains import create_history_aware_retriever, create_retrieval_chain

from chat import GptLLM
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
        self.embedder = OpenAIEmbeddings(api_key="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")
        self.llm = GptLLM().get_llm()
        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base", chunk_size=256, chunk_overlap=0
        )
        # self.chroma = Chroma()
        self.ragchain = None
        self.store = {}

    def extract_documents(self, files):
        for file in files:
            # extension_name = file.filename.split(".")
            extension_name = file.split(".")
            extension_name = extension_name[len(extension_name) - 1]
            if extension_name == "pdf":
                return self._extract_pdf_documents(file)
            elif extension_name == "docx":
                pass

    # TODO First check file type here. if pdf/ weblink / docs etc.

    # Retrieve and generate using the relevant snippets of the blog.

    def _extract_website_content(self, website_urls):
        for url_info in website_urls:
            # if all_links enabled, then do RecursiveCharacterTextSplitter.
            if url_info.get("all_links"):
                pass

            loader = WebBaseLoader(
                url_info.get("url"),
            )
            documents = loader.load()
            # TODO check if webbaseloader ever works or not? Otherwise switch to selenium by default.
            if len(documents[0].page_content.strip(" ")) == 0:
                # TODO We need to use selenium for extraction.
                pass

            # joined_texts = "\n\n".join(tables)
            docs_token = self.text_splitter.split_documents(documents)
            if len(docs_token) > 100:
                # TODO use batching
                pass
            else:
                if self.vectorstore is None:
                    self.vectorstore = Chroma.from_documents(docs_token, embedding=self.embedder)
                    return

                self.vectorstore.add_documents(docs_token)

    def _extract_pdf_documents(self, file_path):
        all_texts = []
        # for file_path in documents_file_path:
        raw_pdf_elements = self.file_utils.extract_pdf_elements(file_path)
        texts = self.file_utils.categorize_elements(raw_pdf_elements)
        # all_texts.append(texts)

        joined_texts = "\n".join(texts)
        texts_4k_token = self.text_splitter.split_text(joined_texts)

        self._add_texts_to_vectorstore(texts_4k_token)

    def _add_texts_to_vectorstore(self, token_text):
        if self.vectorstore is None:
            self.vectorstore = Chroma.from_texts(token_text, embedding=self.embedder, persist_directory="dbstore")
            return
        self.vectorstore.add_texts(texts=token_text)

    def _get_retriever(self):
        if self.vectorstore is None:
            self.vectorstore = Chroma(persist_directory="dbstore", embedding_function=self.embedder)

        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 6})
        return retriever

    def _retrieve_documents(self):
        # vectordb = Chroma(persist_directory="dbstore", embedding_function=self.embedder)
        retriever = self._get_retriever()
        self.rag_chain = (
                {"context": retriever | self.file_utils.format_docs, "question": RunnablePassthrough()}
                | self.prompt
                | self.llm
                | StrOutputParser()
        )

        # return rag_chain

    def chat_with_knowledge_base(self, question):
        self._retrieve_documents()
        for chunk in self.rag_chain.stream(question):
            print(chunk, end="", flush=True)

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def chat_with_history(self, question):
        contextualize_q_system_prompt = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is."""
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self._get_retriever(), contextualize_q_prompt
        )

        # qa_system_prompt = """You are an assistant for question-answering tasks.
        # Use the following pieces of retrieved context to answer the question. If you don't know the answer,
        # just say that you don't know. Try to answer in detail in not less than 100 words.
        # \nQuestion: {question} \nContext: {context} \nAnswer:"""

        qa_system_prompt = """You are an assistant for question-answering tasks. \
        Use the following pieces of retrieved context to answer the question. \
        If you don't know the answer, just say that you don't know. \
        Use three sentences maximum and keep the answer concise.\

        {context}"""

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        # rag_chain = (
        #         {"context": history_aware_retriever | self.file_utils.format_docs, "input": RunnablePassthrough(),
        #          "chat_history": self.get_session_history}
        #         | qa_prompt
        #         | self.llm
        #         | StrOutputParser()
        # )

        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

        for chunk in conversational_rag_chain.stream({"input": question},
                                                     config={"configurable": {"session_id": "abc123"}}):
            print(chunk, end="", flush=True)
