# nscraper

`nscraper` is a small Python package scaffolded for two use cases:

- import it from other projects
- run it directly with `python -m nscraper`

## License

MIT. You can fork, modify, and reuse it with minimal restrictions as long as
the license notice is kept with the software.

## Install

```bash
pip install nscraper
```

For development:

```bash
uv sync --dev
```

## Use as a module

```python
from nscraper import HttpScraper, ScrapeOptions

options = ScrapeOptions(
    url="https://example.com",
    headers={"Accept": "text/html"},
)

content = HttpScraper(options).scrape()
print(content)
```

## Run the Module

```bash
python -m nscraper -u https://example.com -H default
```

Fetch a URL:

```bash
python -m nscraper -u https://example.com -H default
python -m nscraper -u https://example.com -H '{"Accept": "text/html"}'
python -m nscraper -u https://example.com -H default -c cookies.json
python -m nscraper -u https://example.com -H default -t fast -o ~/scraped_data/example.html
python -m nscraper -u https://example.com -H default -o
python -m nscraper -u https://example.com -H default --pretty --print
python -m nscraper -u https://httpbin.org/get -H default -o --pretty --print
python -m nscraper -u https://example.com -H default -t basic
python -m nscraper -u https://example.com -H default --print
python -m nscraper -u https://example.com -H default -o ~/scraped_data/example.html --print
```

## Current API

- `nscraper.ScrapeOptions`
- `nscraper.BaseScraper`
- `nscraper.HttpScraper`
- `nscraper.SeleniumBaseScraper`
- `nscraper.get_scraper(options: ScrapeOptions) -> BaseScraper`
- `nscraper.validate_url(url: str) -> str`
- `nscraper.parse_headers(raw_headers: str | None) -> dict[str, str]`
- `nscraper.load_cookies_file(path: Path | str | None) -> dict[str, str] | None`
- `nscraper.fast_html_transform(content: str) -> str`
- `nscraper.basic_html_transform(content: str) -> str`
- runtime dependency: `niquests==3.18.4`
- runtime dependency: `justhtml==1.14.0`
- development dependency: `pytest`

## Module Flags

- `-u` / `--url` required
- `-H` / `--headers` required, or `default`
- `-e` / `--engine` with `http` or `seleniumbase`
- `-p` / `--proxy`
- `--timeout` default `3`
- `-o` / `--output` writes to a file; bare `-o` uses automatic output, explicit paths must be absolute
- `--print` prints the result to stdout
- `--pretty` pretty-prints the final HTML output
- `-c` / `--cookies-file` optional JSON file
- `-t` / `--transform` with `raw`, `basic`, or `fast`; optional
- `-d` / `--debug` compatibility flag; runtime status lines are printed by default

Behavior:

- invalid or malformed URLs raise `InvalidUrlError`
- missing or malformed headers raise `InvalidHeadersError`
- missing or malformed cookie files raise `InvalidCookiesError`
- use `-H default` to apply the built-in `Accept` and `User-Agent` header dict
- use `-c` only when you want to send cookies; omit it to keep current behavior
- no transform runs unless `-t` / `--transform` is explicitly provided
- no HTML is printed unless `--print` is provided
- when `--output` and `--print` are both provided, stdout prints the written file content
- output files are always overwritten
- missing parent directories for output files are created automatically
- bare `-o` writes to `.nscraper/<netloc>/<path>.<ext>`
- bare `-o` uses `index` for root URLs such as `/`
- bare `-o` preserves nested URL path segments as directories
- bare `-o` appends a short query hash when the URL contains a query string
- explicit output paths must be absolute; relative paths fail immediately
- auto-generated output extensions are content-aware: HTML-like responses use `.html`, JSON responses use `.json`
- `--pretty` formats the final response after the selected transform mode is applied; JSON responses are pretty-printed as JSON
- `raw` returns the fetched supported response with no cleanup
- `fast` removes a small set of noisy elements such as `script`, `style`, `noscript`, `iframe`, and `template` for HTML responses
- `basic` performs heavier cleanup, including hidden elements, head cleanup, and ad-like selectors for HTML responses
- response handling is classified by content type; only HTML and JSON responses are supported
- unsupported content types fail immediately before transform or output is written
- runtime status lines include per-step timings for request, transform, pretty-formatting, and file write operations

Default `User-Agent`:

```text
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36
```

The package is intentionally minimal so you can extend it into a reusable library
and publish it to PyPI.
