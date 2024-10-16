import time


class BatchProcess:

    @classmethod
    def chunk_documents(cls, docs, batch_size):
        """
        Breaks docs into batches
        :param docs:
        :param batch_size:
        :return:
        """
        for i in range(0, len(docs), batch_size):
            yield docs[i:i + batch_size]
