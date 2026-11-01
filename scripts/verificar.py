#!/usr/bin/env python3
"""Confirma que os extratos estão completos e coerentes antes de classificar.

Uso: python verificar.py --config config.json

Verifica, por conta:
  - período coberto e número de meses (é o divisor da média mensal dessa conta);
  - continuidade dos saldos dentro de cada ficheiro (saldo anterior + valor = saldo);
  - buracos entre ficheiros (saldo final de um ≠ saldo inicial do seguinte);
  - meses sem movimentos dentro do período;
  - duplicados removidos entre ficheiros sobrepostos.
Escreve verificacao.md na pasta do config. Termina com código 1 se houver problemas graves.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import cobertura_contas, data_pt, ler_config, meses_entre  # noqa: E402


def fmt(v):
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", " ")


def main(config_path):
    cfg = ler_config(config_path)
    base = Path(cfg["_dir"])
    mov = pd.read_csv(base / "movimentos.csv", dtype={"id": str, "conta": str, "data": str, "descricao": str})
    meta = json.loads((base / "movimentos_meta.json").read_text(encoding="utf-8"))
    cob = cobertura_contas(cfg, mov)
    linhas, graves = ["# Verificação dos extratos", ""], 0
    for c in cfg["contas"]:
        cid = c["id"]
        sub = mov[mov.conta == cid]
        linhas.append(f"## {c.get('nome', cid)} ({c.get('banco', '')}, {cid})")
        if sub.empty:
            linhas += ["- **Sem movimentos.** Confirma os ficheiros desta conta.", ""]
            graves += 1
            continue
        ini, fim, meses = cob[cid]
        fonte = "config" if c.get("inicio") and c.get("fim") else "primeiro e último movimento"
        linhas.append(f"- Período: {ini:%d/%m/%Y} a {fim:%d/%m/%Y} ({fonte}) · **{meses} meses** · {len(sub)} movimentos")
        linhas.append(f"- Entradas {fmt(sub.valor[sub.valor > 0].sum())} · saídas {fmt(sub.valor[sub.valor < 0].sum())}")
        fich = sorted([f for f in meta["ficheiros"] if f.get("conta") == cid], key=lambda f: f.get("de", ""))
        detetados = [f["periodo_detetado"] for f in fich if f.get("periodo_detetado")]
        if detetados and fonte != "config":
            a, b = min(d[0] for d in detetados), max(d[1] for d in detetados)
            linhas.append(f"- Os extratos dizem cobrir {data_pt(a):%d/%m/%Y} a {data_pt(b):%d/%m/%Y}: "
                          f"põe \"inicio\": \"{a}\", \"fim\": \"{b}\" no config para a média usar o período certo.")
        dup = meta["contas"].get(cid, {}).get("duplicados_removidos", 0)
        if dup:
            linhas.append(f"- {dup} movimentos repetidos em ficheiros sobrepostos foram contados uma só vez.")
        sem_saldo = True
        for f in fich:
            ct = f.get("continuidade")
            nome = Path(f["ficheiro"]).name
            if f.get("movimentos", 0) == 0:
                linhas.append(f"- **{nome}: 0 movimentos lidos.**")
                graves += 1
                continue
            if not ct:
                continue
            sem_saldo = False
            if ct["quebras"]:
                graves += 1
                linhas.append(f"- **{nome}: {ct['quebras']} quebras de saldo** (faltam movimentos ou foram mal lidos):")
                linhas += [f"  - {e}" for e in ct["exemplos"]]
            else:
                linhas.append(f"- {nome}: saldos contínuos, de {fmt(ct['saldo_inicial'])} a {fmt(ct['saldo_final'])} "
                              f"(ordem {ct['ordem']}).")
        for f1, f2 in zip(fich, fich[1:]):
            c1, c2 = f1.get("continuidade"), f2.get("continuidade")
            if c1 and c2 and f1.get("a", "") < f2.get("de", "") and abs(c1["saldo_final"] - c2["saldo_inicial"]) > 0.011:
                graves += 1
                linhas.append(f"- **Buraco entre {Path(f1['ficheiro']).name} e {Path(f2['ficheiro']).name}:** saldo final "
                              f"{fmt(c1['saldo_final'])} ≠ saldo inicial {fmt(c2['saldo_inicial'])}. Falta um extrato?")
        if sem_saldo:
            linhas.append("- Os ficheiros não têm saldo: pede ao utilizador o saldo inicial e final do extrato e confirma "
                          "que saldo inicial + entradas + saídas = saldo final.")
            if c["tipo"] == "cartao":
                linhas.append("  Num cartão de crédito, confirma também que os pagamentos recebidos batem com os débitos "
                              "do cartão na conta que o paga.")
        vazios = [m for m in meses_entre(ini, fim) if not sub.data.str.startswith(m).any()]
        if vazios:
            linhas.append(f"- **Meses sem movimentos:** {', '.join(vazios)}. Falta algum extrato?")
            graves += 1
        linhas.append("")
    (base / "verificacao.md").write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))
    print(f"\n{'OK' if not graves else str(graves) + ' problema(s) a resolver'} · relatório em {base / 'verificacao.md'}")
    return 1 if graves else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    sys.exit(main(ap.parse_args().config))
