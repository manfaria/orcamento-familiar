#!/usr/bin/env python3
"""Gera o dashboard "Orçamento Familiar" (um único ficheiro HTML) a partir dos movimentos classificados.

Uso: python construir_dashboard.py --config config.json [--saida Orcamento_Familiar.html]

Escreve também estado.json (última atualização e até quando vai cada conta).
Usa do config.json: familia, pessoas, contribuidores_externos, contas, orcamento (+ orcamento_proposto),
sugestoes, fora_dos_extratos, notas_categorias, notas_movimentos, rendimentos, divisao.metodo,
nota_contribuicoes, nota_extraordinarios e pessoal (detalhe / categorias / total). Usa de analise.json
(se existir): recorrentes, refeicao, imoveis, janela_comum e rendimentos calculados.
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import cobertura_contas, ler_config, mes_completo, meses_entre  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent


def main(config_path, saida=None):
    cfg = ler_config(config_path)
    base = Path(cfg["_dir"])
    df = pd.read_csv(base / "movimentos_classificados.csv", keep_default_na=False, dtype={"id": str, "conta": str, "data": str})
    df["valor"] = df.valor.astype(float)
    cob = cobertura_contas(cfg, df)
    contas = []
    for c in cfg["contas"]:
        if c["id"] not in cob:
            print(f"AVISO: a conta {c['id']} não tem movimentos e fica de fora.")
            continue
        ini, fim, meses = cob[c["id"]]
        contas.append({"id": c["id"], "nome": c.get("nome", c["id"]), "banco": c.get("banco", ""), "tipo": c["tipo"],
                       "titulares": c.get("titulares", []), "uso": c.get("uso", ""), "inicio": ini.isoformat(), "fim": fim.isoformat(), "meses": meses})
    ini = min(dt.date.fromisoformat(c["inicio"]) for c in contas)
    fim = max(dt.date.fromisoformat(c["fim"]) for c in contas)
    i_c = max(dt.date.fromisoformat(c["inicio"]) for c in contas)
    f_c = min(dt.date.fromisoformat(c["fim"]) for c in contas)
    janela = [m for m in meses_entre(i_c, f_c) if mes_completo(m, i_c, f_c)] if i_c <= f_c else []
    analise = {}
    if (base / "analise.json").exists():
        analise = json.loads((base / "analise.json").read_text(encoding="utf-8"))
    ids = {c["id"] for c in contas}
    df = df[df.conta.isin(ids)]
    # privacidade entre o casal: "pessoal": "detalhe" (por omissão), "categorias" (sem descrições) ou "total" (só o total)
    modo = cfg.get("pessoal", "detalhe")
    pessoas_ids = {p["id"] for p in cfg.get("pessoas", [])}
    tx = []
    for r in df.itertuples():
        cat, sub, desc, nota = r.categoria, r.subcategoria, r.descricao, r.nota
        if modo != "detalhe" and r.ambito in pessoas_ids and r.tipo in ("D", "X", "P"):
            desc, nota = "Gasto pessoal", ""
            if modo == "total":
                cat, sub = "Gastos pessoais", ""
        tx.append([r.data, r.conta, r.ambito, r.tipo, cat, sub, round(r.valor, 2), desc, nota, r.contribuinte, r.id])
    recorrentes = analise.get("recorrentes", [])
    if modo != "detalhe":
        recorrentes = [x for x in recorrentes if x.get("ambito") not in pessoas_ids]
    rend = {}
    for p in cfg.get("pessoas", []):
        if cfg.get("rendimentos", {}).get(p["id"]) is not None:
            rend[p["id"]] = {"valor": float(cfg["rendimentos"][p["id"]]), "fonte": "indicado pelo utilizador"}
        elif analise.get("divisao", {}).get("rendimentos", {}).get(p["id"]):
            rend[p["id"]] = analise["divisao"]["rendimentos"][p["id"]]
    data = {
        "familia": cfg.get("familia", ""),
        "gerado_em": dt.date.today().strftime("%d/%m/%Y"),
        "pessoas": [{"id": p["id"], "nome": p.get("nome", p["id"])} for p in cfg.get("pessoas", [])],
        "externos": [{"id": p["id"], "nome": p.get("nome", p["id"])} for p in cfg.get("contribuidores_externos", [])],
        "contas": contas,
        "meses": meses_entre(ini, fim),
        "janela": janela,
        "orcamento": cfg.get("orcamento", []),
        "orcamento_proposto": bool(cfg.get("orcamento_proposto")),
        "sugestoes": cfg.get("sugestoes", []),
        "fora_dos_extratos": cfg.get("fora_dos_extratos", []),
        "notas_categorias": cfg.get("notas_categorias", {}),
        "notas_movimentos": cfg.get("notas_movimentos", {}),
        "nota_contribuicoes": cfg.get("nota_contribuicoes", ""),
        "nota_extraordinarios": cfg.get("nota_extraordinarios", ""),
        "rendimentos": rend,
        "divisao_metodo": (cfg.get("divisao") or {}).get("metodo"),
        "recorrentes": recorrentes[:20],
        "refeicao": analise.get("refeicao", {}),
        "imoveis": analise.get("imoveis", {}),
        "tx": tx,
    }
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tpl = (SKILL / "assets" / "dashboard.html").read_text(encoding="utf-8")
    if "/*__DATA__*/null" not in tpl:
        raise SystemExit("O modelo do dashboard não tem o marcador /*__DATA__*/null.")
    html = tpl.replace("/*__DATA__*/null", js, 1)
    if cfg.get("familia"):
        html = html.replace("<title>Orçamento Familiar</title>", f"<title>Orçamento Familiar · {cfg['familia']}</title>", 1)
    out = Path(saida) if saida else base / "Orcamento_Familiar.html"
    out.write_text(html, encoding="utf-8")
    # estado: o que a atualização mensal e o lembrete agendado consultam para saber o que é novo
    estado = {"atualizado_em": dt.datetime.now().isoformat(timespec="minutes"), "dashboard": out.name,
              "dashboard_url": cfg.get("dashboard_url", ""),
              "periodo": {"inicio": data["meses"][0], "fim": data["meses"][-1]},
              "contas": {c["id"]: {"nome": c["nome"], "inicio": c["inicio"], "fim": c["fim"], "meses": c["meses"],
                                   "movimentos": int((df.conta == c["id"]).sum())} for c in contas},
              "por_identificar": int((df.categoria == "Por identificar").sum())}
    (base / "estado.json").write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Dashboard escrito em {out} ({len(html) // 1024} KB, {len(tx)} movimentos, {len(contas)} contas, "
          f"{len(data['meses'])} meses, janela comum de {len(janela)} meses)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--saida")
    a = ap.parse_args()
    main(a.config, a.saida)
