import shutil
import tempfile
import os
from typing import Optional

import uvicorn
from fastapi import FastAPI, UploadFile, Request, Form
from fastapi.responses import StreamingResponse, FileResponse

from dto.website_detail import WebsiteDetails
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
def create_upload_file(files: list[UploadFile], websites: Optional[str] = Form(None),
                       recursive: Optional[bool] = Form(False)):
    temp_dir = "/tmp/"
    saved_files = []
    websites_list = []
    for file in files:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file_path)

    if len(websites.strip(" ")) != 0:
        websites_list = websites.split("\r\n")
    website_details = WebsiteDetails(websites=websites_list, is_recursive=recursive)
    service.extract_documents(saved_files, website_details)
    # return {"filenames": [file.filename for file in files]}


@app.post("/chatwithme/")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("question", "")
    return StreamingResponse(service.chat_with_knowledge_base(user_message), media_type="text/event-stream")


if __name__ == "__main__":
    # uvicorn.run("__main__:app", reload=True)
    uvicorn.run(app)
