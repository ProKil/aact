from fastapi import FastAPI, Response, File, UploadFile
from fastapi.responses import PlainTextResponse, HTMLResponse, StreamingResponse
from typing import Generator, Dict, Any
from pydantic import BaseModel
import json

app = FastAPI(title="HTTP Test Server")


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Welcome to the HTTP test server"}


# Basic REST endpoints
class Item(BaseModel):
    item_id: int
    name: str


class ItemResponse(BaseModel):
    item: Item
    message: str


@app.get("/items/{item_id}")
async def get_item(item_id: int) -> Item:
    return Item.model_validate({"item_id": item_id, "name": f"Test Item {item_id}"})


@app.post("/items")
async def create_item(item: Item) -> ItemResponse:
    return ItemResponse.model_validate({"message": "Item created", "item": item})


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item) -> ItemResponse:
    return ItemResponse.model_validate(
        {"message": f"Item {item_id} updated", "item": item}
    )


@app.delete("/items/{item_id}")
async def delete_item(item_id: int) -> Dict[str, str]:
    return {"message": f"Item {item_id} deleted"}


# Different content types
@app.get("/text", response_class=PlainTextResponse)
async def get_text() -> str:
    return "This is a plain text response"


@app.get("/html", response_class=HTMLResponse)
async def get_html() -> str:
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Test HTML</title>
        </head>
        <body>
            <h1>HTML Response</h1>
            <p>This is a test HTML response</p>
        </body>
    </html>
    """


@app.get("/binary")
async def get_binary() -> Response:
    content = b"Binary data response"
    return Response(content=content, media_type="application/octet-stream")


class FileResponse(BaseModel):
    filename: str
    content_type: str
    size: int


# File upload
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> FileResponse:
    contents = await file.read()
    return FileResponse.model_validate(
        {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(contents),
        }
    )


# Streaming response
@app.get("/stream")
async def stream_data() -> StreamingResponse:
    def generate() -> Generator[str, None, None]:
        for i in range(5):
            yield json.dumps({"chunk": i}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


# Echo endpoint
@app.post("/echo")
async def echo(request_data: Dict[str, Any]) -> Dict[str, Any]:
    return request_data


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
