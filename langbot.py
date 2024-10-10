from langchain_core.messages import HumanMessage
from langchain_community.document_loaders import WebBaseLoader
import bs4
import time

from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables import RunnablePassthrough
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
#
# import getpass
# import os
# from langchain_openai import ChatOpenAI
#
# # os.environ["OPENAI_API_KEY"] = getpass.getpass()
#
# llm = ChatOpenAI(model="gpt-4o-mini")
#
# # loader = WebBaseLoader(
# #     web_paths=("https://www.sec.gov/cf-frm.pdf",),
# #     bs_kwargs=dict(
# #         parse_only=bs4.SoupStrainer(
# #             class_=("post-content", "post-title", "post-header")
# #         )
# #     ),
# # )
# # docs = loader.load()
#
# # This is a long document we can split up.
# # import requests
# #
# # url = "https://www.sec.gov/cf-frm.pdf"
# # response = requests.get(url)
# # file_Path = 'research_Paper_1.pdf'
# #
# # if response.status_code == 200:
# #     with open(file_Path, 'wb') as file:
# #         file.write(response.content)
# #     print('File downloaded successfully')
# # else:
# #     print('Failed to download file')
#
# # with open("cf-frm.pdf") as f:
# #     state_of_the_union = f.read()
#
# loader = WebBaseLoader("https://www.sec.gov/cf-frm.pdf")
# data = loader.load()
#
# # text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, add_start_index=True)
# text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
#     encoding_name="cl100k_base", chunk_size=512, chunk_overlap=0
# )
# splits = text_splitter.split_documents(data)
# vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())
#
# # Retrieve and generate using the relevant snippets of the blog.
# retriever = vectorstore.as_retriever()
# prompt = hub.pull("rlm/rag-prompt")
#
#
# def format_docs(docs):
#     return "\n\n".join(doc.page_content for doc in docs)
#
#
# rag_chain = (
#         {"context": retriever | format_docs, "question": RunnablePassthrough()}
#         | prompt
#         | llm
#         | StrOutputParser()
# )
#
# for chunk in rag_chain.stream("Help me understand Maximum Inner Product Search in short?"):
#     print(chunk, end="", flush=True)
#
# # response = rag_chain.invoke("Help me understand Maximum Inner Product Search in short?")
# # print(response["answer"])


from langchain_community.document_loaders import RecursiveUrlLoader

loader = RecursiveUrlLoader(
    "https://razorpay.com/docs/api/",
)

docs1 = loader.load()

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base", chunk_size=1024, chunk_overlap=0
)

docs_token = text_splitter.split_documents(docs1)

# embedder = OpenAIEmbeddings()
# vectorstore = Chroma.from_documents(docs_token, embedding=embedder)


embedder = OpenAIEmbeddings()
vectorstore = Chroma(embedding_function=embedder)
# Define Batch Size (Adjust based on your rate limits)
BATCH_SIZE = 100  # Number of documents per batch


# Split documents into batches
def chunk_documents(docs, batch_size):
    for i in range(0, len(docs), batch_size):
        yield docs[i:i + batch_size]


# Function to embed and add to vector store
def embed_and_store(docs_batch):
    try:
        # embeddings = embedder.embed_documents([doc.page_content for doc in docs_batch])
        vectorstore.add_documents(docs_batch)
    except Exception as e:
        print(f"Error embedding batch: {e}")
        time.sleep(5)  # Wait before retrying
        embed_and_store(docs_batch)  # Retry


# Process all documents in batches
for batch in chunk_documents(docs_token, BATCH_SIZE):
    embed_and_store(batch)
    time.sleep(1)  # Delay between batches to respect rate limits
