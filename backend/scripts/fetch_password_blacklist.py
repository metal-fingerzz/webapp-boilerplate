import gzip
from http.client import HTTPResponse
from urllib.request import urlopen

from api.security.passwords import PASSWORD_BLACKLIST_PATH, PASSWORD_BLACKLIST_URL


def main() -> None:
    print(f"Downloading {PASSWORD_BLACKLIST_URL}")
    response: HTTPResponse
    with urlopen(PASSWORD_BLACKLIST_URL) as response:
        raw: str = response.read().decode("utf-8", errors="replace")
        passwords: set[str] = {
            line.lower() for line in raw.splitlines() if len(line) >= 12
        }
        ordered_passwords: list[str] = sorted(passwords)
        PASSWORD_BLACKLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload: bytes = "\n".join(ordered_passwords).encode("utf-8")
        with gzip.GzipFile(
            filename=str(PASSWORD_BLACKLIST_PATH), mode="wb", mtime=0
        ) as file:
            file.write(payload)
        size: int = PASSWORD_BLACKLIST_PATH.stat().st_size
        print(
            f"Wrote {len(ordered_passwords)} entries to {PASSWORD_BLACKLIST_PATH} ({size} bytes)"  # noqa: E501
        )


if __name__ == "__main__":
    main()
