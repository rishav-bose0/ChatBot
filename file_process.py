"""
TODO -
1.Check input type. If web link or physical file.
2.If PDF use extract_pdf_elements.
3. If web link, use webbaseloader/recursive load. Also checkout https://docs.unstructured.io/open-source/core-functionality/partitioning#partition-html
4. DocumentLoaders
"""

from unstructured.partition.pdf import partition_pdf
from langchain_openai import OpenAIEmbeddings


class FileUtils:

    # Extract elements from PDF
    def extract_pdf_elements(self, path):
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
            # max_characters=4000,
            # new_after_n_chars=3800,
            # combine_text_under_n_chars=2000,
            image_output_dir_path=path,
        )

    def categorize_elements(self, raw_pdf_elements):
        """
        Categorize extracted elements from a PDF into tables and texts.
        raw_pdf_elements: List of unstructured.documents.elements
        """
        tables = []
        texts = []
        for element in raw_pdf_elements:
            # if "unstructured.documents.elements.Table" in str(type(element)):
            #     tables.append(str(element))
            # # TODO Check this, this is wrong always.
            # # elif "unstructured.documents.elements.CompositeElement" in str(type(element)):
            # else:
            texts.append(str(element))
        return texts
        # return texts, tables

    # def format_docs(self, docs, max_tokens=120000, encoding_name="cl100k_base"):
    #     encoding = get_encoding(encoding_name)
    #     formatted = ""
    #     total_tokens = 0
    #
    #     for doc in docs:
    #         doc_tokens = len(encoding.encode(doc.page_content))
    #         if total_tokens + doc_tokens > max_tokens:
    #             break
    #         formatted += "\n\n" + doc.page_content
    #         total_tokens += doc_tokens
    #
    #     return formatted

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

# The following is for large documents
# import time
#
# embedder = OpenAIEmbeddings()
# # vectorstore = Chroma(embedding_function=embedder)
# # Define Batch Size (Adjust based on your rate limits)
# BATCH_SIZE = 200  # Number of documents per batch
#
#
# # Split documents into batches
# def chunk_documents(docs, batch_size):
#     for i in range(0, len(docs), batch_size):
#         yield docs[i:i + batch_size]
#
#
# # Function to embed and add to vector store
# def embed_and_store(docs_batch):
#     try:
#         # embeddings = embedder.embed_documents([doc.page_content for doc in docs_batch])
#         vectorstore.add_documents(docs_batch)
#     except Exception as e:
#         print(f"Error embedding batch: {e}")
#         time.sleep(5)  # Wait before retrying
#         embed_and_store(docs_batch)  # Retry
#
#
# # Process all documents in batches
# for batch in chunk_documents(docs_token, BATCH_SIZE):
#     embed_and_store(batch)
#     time.sleep(1)  # Delay between batches to respect rate limits
