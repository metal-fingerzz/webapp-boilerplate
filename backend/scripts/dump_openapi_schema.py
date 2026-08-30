import json
from pathlib import Path
from typing import Any

from api.config import BACKEND_PATH
from api.main import api


def main() -> None:
    openapi_schema: dict[str, Any] = api.openapi()
    output_path: Path = BACKEND_PATH / "openapi-schema.json"
    output_path.write_text(
        json.dumps(openapi_schema, indent=2, ensure_ascii=False) + "\n",
        newline="",
        encoding="utf-8",
    )
    print(f"OpenAPI schema exported -> {output_path}")


if __name__ == "__main__":
    main()
