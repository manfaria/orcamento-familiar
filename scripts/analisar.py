#!/usr/bin/env python3
"""Calcula os factos que sustentam as sugestões de otimização e a divisão justa.

Uso: python analisar.py --config config.json

Lê movimentos_classificados.csv e escreve analise.json com:
  medias            despesa média mensal por âmbito (família e cada pessoa)
  recorrentes       débitos que se repetem com valor estável (custos fixos e subscrições)
  subscricoes       recorrentes de subscrições, telecomunicações e ginásio
  duplicados        o mesmo serviço pago em contas ou planos diferentes
  aumentos          recorrentes cujo valor subiu
  comissoes         comissões e imposto do selo por conta
  numerario         levantamentos (dinheiro sem rasto)
  anuais            despesas anuais que convém reservar por mês
  extraordinarios   movimentos grandes e únicos a confirmar com o utilizador
  tendencias        categorias que subiram nos últimos 3 meses
  orcamento         planeado vs real, por linha (se houver orçamento no config)
  contribuicoes     quanto cada pessoa e contribuidor externo põe na família, por mês
  divisao           divisão igual e proporcional ao rendimento
Os valores são todos tirados dos extratos; nada é estimado.
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import chave, cobertura_contas, conta_por_id, ler_config, mes_completo, meses_entre  # noqa: E402

RUIDO = {"COMPRA", "PAG", "PAGAMENTO", "DD", "DEB", "DEBITO", "DIRETO", "DIRECTO", "TRF", "TRANSF", "TRANSFERENCIA",
         "MB", "WAY", "CONTACTLESS", "PT", "LISBOA", "PORTO", "COM", "WWW", "SA", "LDA", "UNIPESSOAL", "EUR", "POS",
         "TPA", "CARTAO", "VISA", "MASTERCARD", "PAYPAL", "DE", "DA", "DO", "AO", "EM", "PARA", "P", "S"}
NAO_RECORRENTES = {"Numerário", "Partilhas & MB WAY", "Supermercado & alimentação", "Restauração", "Por identificar"}
SUBS = {"Subscrições digitais", "Desporto"}
SUBS_SUB = {"Telecomunicações", "Ginásio & atividades"}
ANUAIS_CAT = {"Seguros", "Impostos & taxas"}


def comerciante(desc):
    d = re.sub(r"\b(APPLE|GOOGLE) PAY\b", " ", chave(desc).upper())
    toks = [t for t in d.split() if t not in RUIDO and not re.search(r"\d", t) and len(t) > 1]
    return " ".join(toks[:2]) or chave(desc).upper()[:20]


def r2(x):
    return round(float(x), 2) + 0.0


def main(config_path):
    cfg = ler_config(config_path)
    base = Path(cfg["_dir"])
    contas = conta_por_id(cfg)
    df = pd.read_csv(base / "movimentos_classificados.csv", keep_default_na=False,
                     dtype={"id": str, "conta": str, "data": str})
    df["valor"] = df.valor.astype(float)
    df["mes"] = df.data.str[:7]
    cob = cobertura_contas(cfg, df)
    meses_conta = {c: v[2] for c, v in cob.items()}
    D = df[df.tipo == "D"].copy()
    D["mensal"] = -D.valor / D.conta.map(meses_conta)
    A = {}
    # médias
    pessoas = [p["id"] for p in cfg.get("pessoas", [])]
    A["medias"] = {amb: r2(D[D.ambito == amb].mensal.sum()) for amb in ["familia"] + pessoas}
    A["medias"]["total"] = r2(D.mensal.sum())
    A["medias_por_categoria_familia"] = {c: r2(v) for c, v in
                                         D[D.ambito == "familia"].groupby("categoria").mensal.sum().sort_values(ascending=False).items()}
    # recorrentes
    D["comerciante"] = D.descricao.map(comerciante)
    rec = []
    for (com, conta), g in D[(D.valor < 0) & ~D.categoria.isin(NAO_RECORRENTES)].groupby(["comerciante", "conta"]):
        por_mes = g.groupby("mes").valor.sum().abs()
        if len(por_mes) < max(3, 0.5 * meses_conta.get(conta, 12)):
            continue
        mn, mx = por_mes.min(), por_mes.max()
        if mx > mn * 1.35 + 1:
            continue
        g = g.sort_values("data")
        meses_cob = meses_conta.get(conta, 12)
        freq = len(por_mes) / max(meses_cob, 1)
        rec.append({"comerciante": com, "conta": conta, "categoria": g.categoria.iloc[-1], "subcategoria": g.subcategoria.iloc[-1],
                    "ambito": g.ambito.iloc[-1], "meses": int(len(por_mes)), "valor_medio": r2(por_mes.mean()),
                    "primeiro": r2(-g.valor.iloc[0]), "ultimo": r2(-g.valor.iloc[-1]),
                    "custo_anual": r2(por_mes.mean() * 12 * min(1, freq + 0.01)), "exemplo": g.descricao.iloc[-1]})
    rec.sort(key=lambda r: -r["custo_anual"])
    A["recorrentes"] = rec
    A["subscricoes"] = [r for r in rec if r["categoria"] in SUBS or r["subcategoria"] in SUBS_SUB]
    A["aumentos"] = [dict(r, aumento_pct=r2((r["ultimo"] / r["primeiro"] - 1) * 100)) for r in rec
                     if r["primeiro"] > 0 and r["ultimo"] > r["primeiro"] * 1.02 + 0.2]
    # duplicados: o mesmo serviço (primeira palavra) em contas diferentes, ou serviços da mesma subcategoria em paralelo
    dup = []
    porpal = defaultdict(list)
    for r in A["subscricoes"]:
        porpal[r["comerciante"].split()[0]].append(r)
    for k, rs in porpal.items():
        if len({r["conta"] for r in rs}) > 1 or len(rs) > 1:
            dup.append({"servico": k, "pagamentos": [{"conta": r["conta"], "valor_medio": r["valor_medio"], "exemplo": r["exemplo"]}
                                                      for r in rs], "custo_anual": r2(sum(r["custo_anual"] for r in rs))})
    porsub = defaultdict(list)
    for r in A["subscricoes"]:
        if r["categoria"] == "Subscrições digitais":
            porsub[r["subcategoria"]].append(r)
    for sub, rs in porsub.items():
        nomes = {r["comerciante"].split()[0] for r in rs}
        if len(nomes) > 1:
            dup.append({"servico": f"vários serviços de {sub}", "pagamentos": [{"conta": r["conta"], "valor_medio": r["valor_medio"],
                        "exemplo": r["exemplo"]} for r in rs], "custo_anual": r2(sum(r["custo_anual"] for r in rs))})
    A["duplicados"] = dup
    # comissões e numerário
    b = D[D.categoria == "Banco & encargos"]
    A["comissoes"] = {c: {"total": r2(-g.valor.sum()), "por_mes": r2(g.mensal.sum()), "por_ano": r2(g.mensal.sum() * 12)}
                      for c, g in b.groupby("conta")}
    n = D[D.categoria == "Numerário"]
    A["numerario"] = {"total": r2(-n.valor.sum()), "por_mes": r2(n.mensal.sum()), "movimentos": int(len(n))}
    # despesas anuais
    an = []
    for (com, conta), g in D[D.categoria.isin(ANUAIS_CAT) & (D.valor < -50)].groupby(["comerciante", "conta"]):
        if g.mes.nunique() <= 2:
            an.append({"comerciante": com, "conta": conta, "categoria": g.categoria.iloc[0], "subcategoria": g.subcategoria.iloc[0],
                       "total": r2(-g.valor.sum()), "reserva_mensal": r2(-g.valor.sum() / 12), "datas": sorted(g.data.tolist())})
    A["anuais"] = an
    # extraordinários a confirmar
    media_fam = max(A["medias"]["familia"], 1)
    recorr = {(r["comerciante"], r["conta"]) for r in rec}
    ex = D[(D.valor < -max(300, 0.15 * media_fam)) & ~D.apply(lambda r: (r.comerciante, r.conta) in recorr, axis=1)]
    A["extraordinarios"] = [{"id": r.id, "data": r.data, "conta": r.conta, "descricao": r.descricao, "valor": r2(r.valor),
                             "categoria": r.categoria} for r in ex.sort_values("valor").itertuples()]
    # tendências (família): últimos 3 meses completos vs anteriores
    todas = [v for v in cob.values()]
    ini_c, fim_c = max(v[0] for v in todas), min(v[1] for v in todas)
    janela = [m for m in meses_entre(ini_c, fim_c) if mes_completo(m, ini_c, fim_c)] if ini_c <= fim_c else []
    fam = D[(D.ambito == "familia") & D.mes.isin(janela)]
    tend = []
    if len(janela) >= 6:
        ult, ant = janela[-3:], janela[:-3]
        for c, g in fam.groupby("categoria"):
            a = -g[g.mes.isin(ant)].valor.sum() / len(ant)
            u = -g[g.mes.isin(ult)].valor.sum() / 3
            if u - a > 30 and (a == 0 or (u / a - 1) > 0.2):
                tend.append({"categoria": c, "media_anterior": r2(a), "media_ultimos_3": r2(u),
                             "variacao_pct": None if a == 0 else r2((u / a - 1) * 100)})
    A["tendencias"] = sorted(tend, key=lambda t: t["media_anterior"] - t["media_ultimos_3"])
    # orçamento
    orc = []
    for linha in cfg.get("orcamento", []):
        amb = linha.get("ambito", "familia")
        g = D[(D.ambito == amb) if amb != "todos" else D.ambito.notna()]
        g = g[g.categoria.isin(linha.get("categorias", []))]
        if linha.get("subcategorias"):
            g = g[g.subcategoria.isin(linha["subcategorias"])]
        real = r2(g.mensal.sum())
        orc.append({"linha": linha["linha"], "planeado": linha["valor"], "real": real, "diferenca": r2(real - linha["valor"])})
    A["orcamento"] = orc
    # contribuições na janela comum (meses completos em todas as contas)
    A["janela_comum"] = janela
    conjuntas = [cid for cid, c in contas.items() if c["tipo"] == "conjunta"]
    ct = df[df.contribuinte.ne("") & df.mes.isin(janela) & df.conta.isin(conjuntas)]
    direto = D[(D.ambito == "familia") & D.mes.isin(janela) & ~D.conta.isin(conjuntas)]
    nm = max(len(janela), 1)
    contrib = {}
    for p in pessoas:
        t = ct[ct.contribuinte == p].valor.sum() / nm
        so_dela = [cid for cid, c in contas.items() if c.get("titulares", []) == [p]]
        d = -direto.loc[direto.conta.isin(so_dela), "valor"].sum() / nm
        contrib[p] = {"para_conjunta": r2(t), "pago_diretamente": r2(d), "total": r2(t + d)}
    for e in cfg.get("contribuidores_externos", []):
        contrib[e["id"]] = {"para_conjunta": r2(ct[ct.contribuinte == e["id"]].valor.sum() / nm), "pago_diretamente": 0.0,
                            "total": r2(ct[ct.contribuinte == e["id"]].valor.sum() / nm), "externo": True}
    gasto_fam = r2(-D[(D.ambito == "familia") & D.mes.isin(janela)].valor.sum() / nm)
    A["contribuicoes"] = {"meses": nm, "por_pessoa": contrib, "despesa_familia": gasto_fam,
                          "total": r2(sum(v["total"] for v in contrib.values())),
                          "saldo": r2(sum(v["total"] for v in contrib.values()) - gasto_fam)}
    # divisão justa
    ext = sum(v["total"] for v in contrib.values() if v.get("externo"))
    a_dividir = max(gasto_fam - ext, 0)
    rend = {}
    for p in pessoas:
        if cfg.get("rendimentos", {}).get(p) is not None:
            rend[p] = {"valor": float(cfg["rendimentos"][p]), "fonte": "indicado pelo utilizador"}
        else:
            so_dela = [cid for cid, c in contas.items() if c.get("titulares", []) == [p]]
            sal = df[(df.tipo == "R") & df.subcategoria.str.contains("Salário|Sal[áa]rio|Vencimento", case=False, regex=True)
                     & df.conta.isin(so_dela)]
            if len(sal):
                v = sum(g.valor.sum() / meses_conta[c] for c, g in sal.groupby("conta"))
                rend[p] = {"valor": r2(v), "fonte": "salários nos extratos"}
    div = {"a_dividir": r2(a_dividir), "contribuicoes_externas": r2(ext), "rendimentos": rend, "metodos": {}}
    if pessoas:
        div["metodos"]["igual"] = {p: r2(a_dividir / len(pessoas)) for p in pessoas}
        if len(rend) == len(pessoas) and sum(r["valor"] for r in rend.values()) > 0:
            tot = sum(r["valor"] for r in rend.values())
            div["metodos"]["proporcional"] = {p: r2(a_dividir * rend[p]["valor"] / tot) for p in pessoas}
    A["divisao"] = div
    # por identificar
    q = D[D.categoria == "Por identificar"]
    A["por_identificar"] = {"movimentos": int(len(q)), "por_mes": r2(q.mensal.sum())}
    (base / "analise.json").write_text(json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
    imprimir(A)


def imprimir(A):
    print("Médias mensais:", A["medias"])
    print(f"Subscrições ({len(A['subscricoes'])}):")
    for r in A["subscricoes"]:
        print(f"  {r['comerciante']:<22} {r['conta']:<12} {r['valor_medio']:>8.2f} €/mês · {r['custo_anual']:>8.2f} €/ano")
    for d in A["duplicados"]:
        print(f"Possível duplicado: {d['servico']} · {d['custo_anual']:.2f} €/ano · {[p['exemplo'] for p in d['pagamentos']]}")
    for r in A["aumentos"]:
        print(f"Aumento: {r['comerciante']} {r['primeiro']:.2f} → {r['ultimo']:.2f} (+{r['aumento_pct']}%)")
    print("Comissões:", A["comissoes"])
    print("Numerário:", A["numerario"])
    for a in A["anuais"]:
        print(f"Anual: {a['comerciante']} {a['total']:.2f} € → reservar {a['reserva_mensal']:.2f} €/mês")
    for e in A["extraordinarios"]:
        print(f"Extraordinário? {e['data']} {e['conta']} {e['descricao']} {e['valor']:.2f}")
    for t in A["tendencias"]:
        print(f"Tendência: {t['categoria']} {t['media_anterior']:.2f} → {t['media_ultimos_3']:.2f} €/mês")
    c = A["contribuicoes"]
    print(f"Contribuições ({c['meses']} meses comuns): {c['por_pessoa']} · despesa da família {c['despesa_familia']} · saldo {c['saldo']}")
    print("Divisão:", A["divisao"]["metodos"], "rendimentos:", A["divisao"]["rendimentos"])
    print("Por identificar:", A["por_identificar"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    main(ap.parse_args().config)
