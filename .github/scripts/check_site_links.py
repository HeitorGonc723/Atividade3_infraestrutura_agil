from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[2]
PAGES = ("index.html", "quem-somos.html", "contato.html")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.references = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])

        for attribute in ("href", "src"):
            value = attributes.get(attribute)
            if value:
                self.references.append(value)


def main():
    errors = []
    parsers = {}

    for page in PAGES:
        path = ROOT / page
        if not path.is_file():
            errors.append(f"{page}: página obrigatória não encontrada")
            continue

        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
        parsers[page] = parser

    for page, parser in parsers.items():
        source = ROOT / page
        for reference in parser.references:
            url = urlsplit(reference)
            if url.scheme or url.netloc:
                continue

            relative_path = unquote(url.path)
            if relative_path.startswith("/"):
                target = (ROOT / relative_path.lstrip("/")).resolve()
            else:
                target = (source.parent / relative_path).resolve() if relative_path else source

            try:
                target.relative_to(ROOT)
            except ValueError:
                errors.append(f"{page}: referência fora do projeto: {reference}")
                continue

            if not target.is_file():
                errors.append(f"{page}: arquivo referenciado não encontrado: {reference}")
                continue

            if url.fragment and target.suffix.lower() == ".html":
                target_page = target.relative_to(ROOT).as_posix()
                target_parser = parsers.get(target_page)
                if target_parser is None:
                    target_parser = PageParser()
                    target_parser.feed(target.read_text(encoding="utf-8"))
                    target_parser.close()
                    parsers[target_page] = target_parser

                if unquote(url.fragment) not in target_parser.ids:
                    errors.append(f"{page}: âncora não encontrada: {reference}")

    if errors:
        print("\n".join(errors))
        raise SystemExit(1)

    print("Páginas e links locais validados com sucesso.")


if __name__ == "__main__":
    main()
