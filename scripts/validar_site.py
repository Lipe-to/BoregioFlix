"""Verifica referências locais das páginas e folhas de estilo do site."""

from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
errors = []
checked = 0


def check_reference(source, reference):
    global checked
    if not reference:
        return
    parts = urlsplit(reference.strip())
    if parts.scheme or parts.netloc or not parts.path:
        return
    path = unquote(parts.path)
    if path.startswith("/"):
        errors.append(f"{source.relative_to(ROOT)}: caminho absoluto não suportado: {reference}")
        return
    target = (source.parent / path).resolve()
    if not target.is_relative_to(ROOT):
        errors.append(f"{source.relative_to(ROOT)}: referência fora do site: {reference}")
        return
    checked += 1
    if not target.is_file():
        errors.append(f"{source.relative_to(ROOT)}: arquivo não encontrado: {reference}")


class References(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.source = source

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in {"src", "href"}:
                check_reference(self.source, value)


if not (ROOT / "index.html").is_file():
    errors.append("index.html não encontrado")

for file in sorted(ROOT.glob("*.html")):
    parser = References(file)
    parser.feed(file.read_text(encoding="utf-8"))
    parser.close()

for file in sorted(ROOT.glob("*.css")):
    for match in CSS_URL.finditer(file.read_text(encoding="utf-8")):
        check_reference(file, match.group(2))

if errors:
    print("Falha na validação:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(f"Validação concluída: {checked} referências locais verificadas.")

