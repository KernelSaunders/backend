import uvicorn

from src.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port, reload=True)


if __name__ == "__main__":
    main()
