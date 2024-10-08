from unstructured.partition.pdf import partition_pdf
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
import os
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings


# Extract elements from PDF
def extract_pdf_elements(path):
    """
    Extract images, tables, and chunk text from a PDF file.
    path: File path, which is used to dump images (.jpg)
    fname: File name
    """
    return partition_pdf(
        filename=path,
        strategy='hi_res',
        extract_images_in_pdf=False,
        infer_table_structure=True,
        hi_res_model_name='yolox',
        # chunking_strategy="by_title",
        max_characters=4000,
        new_after_n_chars=3800,
        combine_text_under_n_chars=2000,
        image_output_dir_path=path,
    )


def categorize_elements(raw_pdf_elements):
    """
    Categorize extracted elements from a PDF into tables and texts.
    raw_pdf_elements: List of unstructured.documents.elements
    """
    tables = []
    texts = []
    for element in raw_pdf_elements:
        if "unstructured.documents.elements.Table" in str(type(element)):
            tables.append(str(element))
        elif "unstructured.documents.elements.CompositeElement" in str(type(element)):
            texts.append(str(element))
    return texts, tables


def format_docs(docs, max_tokens=120000, encoding_name="cl100k_base"):
    encoding = get_encoding(encoding_name)
    formatted = ""
    total_tokens = 0

    for doc in docs:
        doc_tokens = len(encoding.encode(doc.page_content))
        if total_tokens + doc_tokens > max_tokens:
            break
        formatted += "\n\n" + doc.page_content
        total_tokens += doc_tokens

    return formatted


os.environ["OPENAI_API_KEY"] = "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"

llm = ChatOpenAI(model="gpt-4o-mini")
fname = "mahindra_report.pdf"

# Get elements
raw_pdf_elements = extract_pdf_elements(fname)

# Get text, tables
texts, tables = categorize_elements(raw_pdf_elements)

text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base", chunk_size=256, chunk_overlap=0
)

joined_texts = " ".join(texts)
texts_4k_token = text_splitter.split_text(joined_texts)

embedder = OpenAIEmbeddings()
vectorstore = Chroma.from_texts(texts_4k_token, embedding=embedder)

# Retrieve and generate using the relevant snippets of the blog.
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
prompt = hub.pull("rlm/rag-prompt")

from tiktoken import get_encoding

rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
)

for chunk in rag_chain.stream(
        "What was the Income from investment related to subsidiaries, associates, and joint ventures in F24 and F23"):
    print(chunk, end="", flush=True)
