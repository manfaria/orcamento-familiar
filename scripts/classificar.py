#!/usr/bin/env python3
"""Classifica os movimentos: tipo, categoria, subcategoria, âmbito e contribuinte.

Uso: python classificar.py --config config.json

Lê movimentos.csv e regras.csv (se não existir, copia as regras base da skill). Ordem de decisão,
a primeira que encaixa ganha:
  1. regras de regras.csv com id_movimento (decisões sobre um movimento concreto);
  2. pares de transferências entre contas da família e pagamentos de cartão (mesmo valor, sinal
     contrário, até 4 dias de diferença);
  3. nomes das pessoas e dos contribuidores externos (campo nomes_banco no config);
  4. restantes regras de regras.csv, por ordem;
  5. o que sobra fica "Por identificar".
Escreve movimentos_classificados.csv e por_identificar.csv.
"""
import argparse
import csv
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import COLS_CLASS, ambito_padrao, chave, conta_por_id, data_pt, ler_config  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
TRANSF = re.compile(r"\b(?:TRF|TRANSF|TRANSFER[EÊ]NCIA|MB ?WAY|SEPA|ENTRE CONTAS|P/|PARA|DE|RECEBID|EMITID|"
                    r"PAGAMENTO|PAG\.?|CART[ÃA]O|LIQUIDA|DEP[ÓO]SITO|IMED)", re.I)


def ler_regras(caminho):
    linhas = [l for l in open(caminho, encoding="utf-8") if l.strip() and not l.lstrip().startswith("#")]
    regras = []
    for n, r in enumerate(csv.DictReader(linhas), start=1):
        r = {k: (v or "").strip() for k, v in r.items() if k}
        if not r.get("padrao") and not r.get("id_movimento"):
            continue
        r["_n"] = n
        r["_rx"] = re.compile(r["padrao"], re.I) if r.get("padrao") else None
        for k in ("valor_min", "valor_max"):
            r[k] = float(r[k].replace(",", ".")) if r.get(k) else None
        for k in ("data_de", "data_ate"):
            r[k] = data_pt(r[k]).isoformat() if r.get(k) else None
        regras.append(r)
    return regras


def conta_ok(regra, conta):
    if not regra.get("conta"):
        return True
    for alvo in regra["conta"].split("|"):
        alvo = alvo.strip()
        if alvo == conta["id"] or (alvo.startswith("tipo:") and alvo[5:] == conta["tipo"]):
            return True
    return False


def encaixa(regra, m, conta):
    if not conta_ok(regra, conta):
        return False
    v = m["valor"]
    if regra.get("sinal") == "saida" and v >= 0:
        return False
    if regra.get("sinal") == "entrada" and v <= 0:
        return False
    if regra["valor_min"] is not None and abs(v) < regra["valor_min"] - 0.004:
        return False
    if regra["valor_max"] is not None and abs(v) > regra["valor_max"] + 0.004:
        return False
    if regra["data_de"] and m["data"] < regra["data_de"]:
        return False
    if regra["data_ate"] and m["data"] > regra["data_ate"]:
        return False
    return bool(regra["_rx"].search(m["descricao"])) if regra["_rx"] else True


def aplicar_regra(regra, m, conta, origem):
    return {"tipo": regra.get("tipo") or "D", "categoria": regra.get("categoria", ""),
            "subcategoria": regra.get("subcategoria", ""), "ambito": regra.get("ambito") or ambito_padrao(conta),
            "contribuinte": regra.get("contribuinte", ""), "nota": regra.get("nota", ""), "regra": origem}


def nomes(cfg):
    """[(id, nome, tipo, regex)] para pessoas e contribuidores externos."""
    out = []
    for grupo, tipo in (("pessoas", "pessoa"), ("contribuidores_externos", "externo")):
        for p in cfg.get(grupo, []):
            ns = [n for n in p.get("nomes_banco", []) if n.strip()]
            if ns:
                rx = re.compile("|".join(re.escape(chave(n)).replace(r"\ ", r"\s+") for n in ns), re.I)
                out.append((p["id"], p.get("nome", p["id"]), tipo, rx))
    return out


def detetar_pares(df, contas):
    """Emparelha saídas e entradas do mesmo valor em contas diferentes da família."""
    res = {}
    cartoes = [cid for cid, c in contas.items() if c["tipo"] == "cartao"]
    cand = df[df.descricao.str.contains(TRANSF) | df.conta.isin(cartoes)]
    entradas = defaultdict(list)
    for i, m in cand[cand.valor > 0].iterrows():
        entradas[round(m.valor, 2)].append(i)
    usadas = set()
    for i, o in cand[cand.valor < 0].sort_values("data").iterrows():
        melhor = None
        for j in entradas.get(round(-o.valor, 2), []):
            if j in usadas:
                continue
            e = df.loc[j]
            if e.conta == o.conta:
                continue
            dd = abs((pd.Timestamp(e.data) - pd.Timestamp(o.data)).days)
            if dd <= 4 and (melhor is None or dd < melhor[0]):
                melhor = (dd, j)
        if not melhor:
            continue
        j = melhor[1]
        usadas.add(j)
        res.update(classificar_par(i, o, j, df.loc[j], contas))
    return res


def classificar_par(i, o, j, e, contas):
    A, B = contas[o.conta], contas[e.conta]
    tA, tB = A.get("titulares", []), B.get("titulares", [])
    base = {"ambito": "familia", "nota": "", "regra": "par"}
    def T(cat, sub="", contrib="", tipo="T", amb=None, conta=None):
        return dict(base, tipo=tipo, categoria=cat, subcategoria=sub, contribuinte=contrib,
                    ambito=amb or (ambito_padrao(conta) if conta else "familia"))
    if B["tipo"] == "cartao" or A["tipo"] == "cartao":
        return {i: T("Pagamento de cartão", B.get("nome", ""), tipo="C", conta=A),
                j: T("Pagamento de cartão", A.get("nome", ""), tipo="C", conta=B)}
    if A["tipo"] == "conjunta" and B["tipo"] == "conjunta":
        return {i: T("Transferência interna", "Entre contas conjuntas"), j: T("Transferência interna", "Entre contas conjuntas")}
    if A["tipo"] != "conjunta" and B["tipo"] == "conjunta":
        p = tA[0] if len(tA) == 1 else ""
        return {i: T("Transferência interna", "Para a conta conjunta", conta=A),
                j: T("Contribuição", p, contrib=p)}
    if A["tipo"] == "conjunta" and B["tipo"] != "conjunta":
        p = tB[0] if len(tB) == 1 else ""
        return {i: T("Transferência para pessoa", p, contrib=p), j: T("Transferência interna", "Recebido da conta conjunta", conta=B)}
    if set(tA) == set(tB):
        return {i: T("Transferência interna", "Entre contas da mesma pessoa", conta=A),
                j: T("Transferência interna", "Entre contas da mesma pessoa", conta=B)}
    return {i: T("Transferência interna", "Entre pessoas da família", conta=A),
            j: T("Transferência interna", "Entre pessoas da família", conta=B)}


def por_nome(m, conta, lista):
    d = chave(m["descricao"])
    for pid, nome, tipo, rx in lista:
        if not rx.search(d):
            continue
        tit = conta.get("titulares", [])
        if conta["tipo"] == "conjunta":
            if m["valor"] > 0:
                return {"tipo": "T" if tipo == "pessoa" else "R", "categoria": "Contribuição", "subcategoria": pid,
                        "ambito": "familia", "contribuinte": pid, "nota": "", "regra": "nome"}
            if tipo == "pessoa":
                return {"tipo": "T", "categoria": "Transferência para pessoa", "subcategoria": pid, "ambito": "familia",
                        "contribuinte": pid, "nota": "", "regra": "nome"}
        elif tipo == "pessoa":
            if pid in tit:
                return {"tipo": "P", "categoria": "Poupança & investimento", "subcategoria": "Conta própria fora da análise",
                        "ambito": ambito_padrao(conta), "contribuinte": "", "regra": "nome",
                        "nota": "Transferência para outra conta da mesma pessoa que não está nos extratos: confirmar"}
            return {"tipo": "T", "categoria": "Transferência interna", "subcategoria": "Entre pessoas da família",
                    "ambito": ambito_padrao(conta), "contribuinte": "", "nota": "", "regra": "nome"}
        elif tipo == "externo" and m["valor"] > 0:
            return {"tipo": "R", "categoria": "Rendimentos", "subcategoria": "Ajuda de " + nome, "ambito": ambito_padrao(conta),
                    "contribuinte": "", "nota": "", "regra": "nome"}
    return None


def main(config_path):
    cfg = ler_config(config_path)
    base = Path(cfg["_dir"])
    regras_path = base / "regras.csv"
    if not regras_path.exists():
        shutil.copy(SKILL / "assets" / "regras_base.csv", regras_path)
        print(f"Criei {regras_path} a partir das regras base.")
    regras = ler_regras(regras_path)
    por_id = {r["id_movimento"]: r for r in regras if r.get("id_movimento")}
    gerais = [r for r in regras if not r.get("id_movimento")]
    contas = conta_por_id(cfg)
    df = pd.read_csv(base / "movimentos.csv", dtype={"id": str, "conta": str, "data": str, "descricao": str,
                                                    "ficheiro": str}, keep_default_na=False)
    df["valor"] = df.valor.astype(float)
    pares = detetar_pares(df[~df.id.isin(por_id)], contas)
    lista_nomes = nomes(cfg)
    amb_cat = cfg.get("ambito_por_categoria", {})
    regra_por_n = {f"regras.csv:{r['_n']}": r for r in gerais}
    out = []
    for i, m in df.iterrows():
        conta = contas[m.conta]
        c = None
        if m.id in por_id:
            c = aplicar_regra(por_id[m.id], m, conta, "regras.csv:id")
        elif i in pares:
            c = pares[i]
        else:
            c = por_nome(m, conta, lista_nomes)
            if c is None:
                for r in gerais:
                    if encaixa(r, m, conta):
                        c = aplicar_regra(r, m, conta, f"regras.csv:{r['_n']}")
                        break
        if c is None:
            c = {"tipo": "D" if m.valor < 0 else "R", "categoria": "Por identificar", "subcategoria": "",
                 "ambito": ambito_padrao(conta), "contribuinte": "", "nota": "", "regra": "por identificar"}
        # categorias que são sempre da família, mesmo pagas de contas pessoais (útil sem conta conjunta)
        explicito = c["regra"].startswith("regras.csv") and (por_id.get(m.id) or regra_por_n.get(c["regra"], {})).get("ambito")
        if c["tipo"] == "D" and conta["tipo"] != "conjunta" and not explicito and c["categoria"] in amb_cat:
            c["ambito"] = amb_cat[c["categoria"]]
        out.append({**m.to_dict(), **c})
    res = pd.DataFrame(out)
    # pagamentos de cartão sem extrato do cartão: são despesa (sem detalhe), não podem desaparecer
    pagos = {c.get("pago_por") for c in cfg["contas"] if c["tipo"] == "cartao"}
    sem_cartao = [cid for cid, c in contas.items() if c["tipo"] != "cartao" and cid not in pagos]
    orfaos = (res.tipo == "C") & (res.regra != "par") & res.conta.isin(sem_cartao)
    res.loc[orfaos, ["tipo", "categoria", "subcategoria", "nota"]] = [
        "D", "Cartão de crédito sem extrato", "", "Pagamento de um cartão cujo extrato não foi incluído: pedir o extrato"]
    res = res[COLS_CLASS]
    res.to_csv(base / "movimentos_classificados.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    # por identificar, com contexto
    q = res[res.categoria == "Por identificar"].copy()
    ctx = []
    for _, m in q.iterrows():
        mesmo = res[(res.data == m.data) & (res.id != m.id)]
        ctx.append(" · ".join(f"{r.conta}: {r.descricao[:30]} {r.valor:.2f}" for _, r in mesmo.head(4).iterrows()))
    q["mesmo_dia"] = ctx
    q["parecidos"] = q.descricao.map(lambda d: int((res.descricao == d).sum()))
    q = q.reindex(q.valor.abs().sort_values(ascending=False).index)
    q[["id", "conta", "data", "descricao", "valor", "parecidos", "mesmo_dia"]].to_csv(base / "por_identificar.csv", index=False)
    resumo(res, orfaos.sum(), base)


def resumo(res, orfaos, base):
    print(f"{len(res)} movimentos classificados → {base / 'movimentos_classificados.csv'}")
    print("Por tipo:")
    for t, g in res.groupby("tipo"):
        print(f"  {t}: {len(g):>5} movimentos · {g.valor.sum():>12.2f} €")
    d = res[res.tipo == "D"]
    tot = -d.valor.sum()
    if tot:
        print("Despesa por categoria (total do período):")
        for c, v in (-d.groupby("categoria").valor.sum()).sort_values(ascending=False).items():
            print(f"  {c:<34} {v:>10.2f} € {v / tot * 100:5.1f}%")
    q = res[res.categoria == "Por identificar"]
    print(f"Por identificar: {len(q)} movimentos · {-q.valor[q.valor < 0].sum():.2f} € de saídas "
          f"({(-q.valor[q.valor < 0].sum()) / tot * 100 if tot else 0:.1f}% da despesa) · "
          f"{q.valor[q.valor > 0].sum():.2f} € de entradas → por_identificar.csv")
    if orfaos:
        print(f"AVISO: {orfaos} pagamentos de cartão sem o extrato do cartão (ficaram como despesa sem detalhe).")
    sem = res[(res.tipo == "T") & (res.categoria == "Contribuição") & (res.contribuinte == "")]
    if len(sem):
        print(f"AVISO: {len(sem)} contribuições sem pessoa associada (contas com vários titulares).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    main(ap.parse_args().config)
