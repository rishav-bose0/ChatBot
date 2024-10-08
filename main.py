import uvicorn
from fastapi import FastAPI, UploadFile

from service import Service

app = FastAPI()
service = Service()

@app.post("/extract")
def extract_info_from_docs():
    pass


@app.post("/uploadfile/")
def create_upload_file(files: list[UploadFile]):
    service.extract_documents()
    return {"filenames": [file.filename for file in files]}


@app.post("/chat/")
def chat(question: str):
    return service.chat_with_knowledge_base(question)


if __name__ == "__main__":
    # uvicorn.run("__main__:app", reload=True)
    uvicorn.run(app)
