# nscraper

`nscraper` is a small Python package scaffolded for two use cases:

- import it from other projects
- run it directly with `python -m nscraper`

## Install

```bash
pip install nscraper
```

For development:

```bash
pip install -e ".[dev]"
```

## Use as a module

```python
from nscraper import hello

print(hello("world"))
```

## Run from the command line

```bash
python -m nscraper
nscraper
```

Fetch a URL:

```bash
python -m nscraper -u https://example.com -H default
python -m nscraper -u https://example.com -H '{"Accept": "text/html"}'
python -m nscraper -u https://example.com -H default -c cookies.json
```

## Current API

- `nscraper.hello(name: str = "world") -> str`
- `nscraper.validate_url(url: str) -> str`
- `nscraper.parse_headers(raw_headers: str | None) -> dict[str, str]`
- `nscraper.fetch_url(url: str, *, headers: dict[str, str], timeout: float = 3.0, proxy: str | None = None) -> str`
- `nscraper.run_scrape(options: ScrapeOptions) -> str`
- runtime dependency: `niquests==3.18.4`
- runtime dependency: `justhtml==1.9.1`
- development dependency: `pytest`

## CLI

Required:

- `-u` / `--url`
- `-H` / `--headers`

Optional:

- `-e` / `--engine` with `http` or `seleniumbase`
- `-p` / `--proxy`
- `--timeout` default `3`
- `-o` / `--output`
- `-c` / `--cookies-file` optional JSON file
- `-t` / `--transform` default `raw`

Behavior:

- invalid or malformed URLs raise `InvalidUrlError`
- missing or malformed headers raise `InvalidHeadersError`
- missing or malformed cookie files raise `InvalidCookiesError`
- use `-H default` to apply the built-in `Accept` and `User-Agent` header dict
- use `-c` only when you want to send cookies; omit it to keep current behavior
- output files are always overwritten
- `basic_html` removes HTML tags and writes the transformed content

Default `User-Agent`:

```text
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36
```

The package is intentionally minimal so you can extend it into a reusable library
and publish it to PyPI.
