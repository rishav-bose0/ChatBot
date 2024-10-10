import uvicorn
from fastapi import FastAPI, UploadFile, Request
from fastapi.responses import StreamingResponse, FileResponse
from service import Service

app = FastAPI()
service = Service()


# TODO complete the extract part.
@app.post("/extract")
def extract_info_from_docs():
    pass


@app.get("/upload")
async def root():
    return FileResponse("static/upload.html")


@app.get("/chat")
async def root():
    return FileResponse("static/chat.html")


@app.post("/uploadfile/")
def create_upload_file(files: list[UploadFile]):
    service.extract_documents()
    return {"filenames": [file.filename for file in files]}


@app.post("/chatwithme/")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "")
    return StreamingResponse(service.chat_with_knowledge_base(user_message), media_type="text/event-stream")


if __name__ == "__main__":
    # uvicorn.run("__main__:app", reload=True)
    uvicorn.run(app)
