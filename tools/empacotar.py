#!/usr/bin/env python3
"""Gera os dois zips de instalação em dist/ a partir dos ficheiros do repositório.

Uso (na raiz do repositório): python tools/empacotar.py

  dist/orcamento-familiar-claude.zip  pasta orcamento-familiar/ na raiz (Claude)
  dist/orcamento-familiar.zip         SKILL.md na raiz (ChatGPT, Gemini, Microsoft 365 Copilot)

Ficam de fora tools/, dist/ e os ficheiros do git. Corre isto antes de cada commit que mude a skill.
"""
import subprocess
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOME = "orcamento-familiar"
FORA = ("tools/", "dist/", ".github/", ".gitignore")

ficheiros = [f for f in subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True)
             .stdout.splitlines() if not f.startswith(FORA)]
(RAIZ / "dist").mkdir(exist_ok=True)
for destino, prefixo in ((f"{NOME}-claude.zip", f"{NOME}/"), (f"{NOME}.zip", "")):
    with zipfile.ZipFile(RAIZ / "dist" / destino, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(ficheiros):
            z.write(RAIZ / f, prefixo + f)
    print(f"dist/{destino}: {len(ficheiros)} ficheiros")
skill = (RAIZ / "SKILL.md").read_text(encoding="utf-8")
print(f"SKILL.md: {len(skill)} caracteres (limite do Microsoft 365 Copilot: 20 000)")
