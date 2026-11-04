
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.api.routes import router


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {"message": "Claritax API is running"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        openapi_version="3.0.3",
    )

    upload_path = f"{settings.api_prefix}/documents/upload"

    # Locate the upload request body schema
    request_body_schema = (
        openapi_schema["paths"][upload_path]["post"]
        ["requestBody"]["content"]["multipart/form-data"]
        ["schema"]
    )

    schema_ref = request_body_schema.get("$ref")

    if schema_ref:
        schema_name = schema_ref.split("/")[-1]

        body_schema = openapi_schema["components"]["schemas"][
            schema_name
        ]

        # Explicitly configure files as binary uploads
        body_schema["properties"]["files"] = {
            "type": "array",
            "items": {
                "type": "string",
                "format": "binary",
            },
            "title": "Files",
        }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
