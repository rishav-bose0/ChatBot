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
        # tables = []
        texts = []
        for element in raw_pdf_elements:
            # Uncomment this if only want tabular info from the pdf.
            # if "unstructured.documents.elements.Table" in str(type(element)):
            #     tables.append(str(element))
            texts.append(str(element))
        return texts

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
