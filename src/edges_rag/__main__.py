import uvicorn

from edges_rag.app import create_app
from edges_rag.config import get_settings


def main() -> None:
    settings = get_settings()
    application = create_app(settings=settings, skip_lifespan_index=False)
    uvicorn.run(application, host=settings.rag_host, port=settings.rag_port)


if __name__ == "__main__":
    main()
