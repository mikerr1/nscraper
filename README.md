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
- `basic_html` removes non-content elements and writes cleaned HTML output

Default `User-Agent`:

```text
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36
```

The package is intentionally minimal so you can extend it into a reusable library
and publish it to PyPI.

## GitHub And PyPI Release Flow

- pull requests to `master` run tests in GitHub Actions
- published GitHub releases run tests, build `sdist` and `wheel`, then publish to PyPI
- the publish workflow is in [.github/workflows/release.yml](/home/ubuntu/projects/nscraper/.github/workflows/release.yml)

Before the release workflow can publish, configure Trusted Publishing in PyPI:

1. create the project on PyPI if it does not exist yet
2. in PyPI, open the project publishing settings
3. add a trusted publisher for this GitHub repository
4. use the `release` workflow on the `master` branch

After that, the normal flow is:

1. push code to GitHub
2. merge to `master`
3. create a GitHub release for the version tag
4. let GitHub Actions test, build, and publish the package
