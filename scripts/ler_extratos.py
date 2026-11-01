#!/usr/bin/env python3
"""Lê extratos bancários (CSV, XLSX, XLS ou PDF) e junta-os num formato único.

Uso:
  python ler_extratos.py --inspecionar CAMINHO          # mostra o que o script percebe de um ficheiro
  python ler_extratos.py --config config.json            # lê as contas do config e escreve movimentos.csv

Cada conta do config.json indica os ficheiros em "ficheiros" (padrões glob relativos à pasta do config,
ou objetos {"padrao": "...", "desde": "AAAA-MM-DD", "ate": "AAAA-MM-DD"}). Opcionalmente:
  "sinal": "invertido"   para cartões que listam compras como valores positivos
  "mapa": {...}          para forçar colunas (linha_cabecalho, data, descricao, valor, debito, credito,
                         saldo, sinal_col, formato_data, folha)
  "parser": "parsers/x.py"  módulo próprio com a função ler(caminho) -> lista de dicts
                            {data, descricao, valor, saldo}
"""
import argparse
import csv
import glob
import importlib.util
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import COLS_MOV, chave, data_pt, id_movimento, inicio_janela, ler_config, num_pt  # noqa: E402

DATE_KEYS = ["data mov", "data lanc", "data oper", "data transa", "data de mov", "data da opera", "data contab",
             "data compra", "data", "date", "dt"]
DESC_KEYS = ["descri", "descritivo", "movimento", "historico", "designacao", "detalhe", "concept", "narrativa",
             "description", "referencia", "operacao", "estabelecimento", "comerciante", "texto"]
AMOUNT_KEYS = ["montante", "valor", "importancia", "quantia", "amount", "total"]
DEBIT_KEYS = ["debito", "debit", "levantamento", "saida", "pagamento", "despesa"]
CREDIT_KEYS = ["credito", "credit", "deposito", "entrada", "recebimento", "receita"]
SALDO_KEYS = ["saldo contab", "saldo apos", "saldo final", "saldo", "balance"]
SIGN_KEYS = ["d c", "dc", "natureza", "sinal", "tipo mov", "debito credito", "credito debito"]
RESUMO = re.compile(r"^\s*(saldo (inicial|final|anterior|disponivel|contabilistico)|total|transporte|a transportar)\b",
                    re.I)


# ------------------------------------------------------------------ leitura bruta
def linhas_csv(caminho):
    raw = Path(caminho).read_bytes()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            txt = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    amostra = "\n".join(txt.splitlines()[:60])
    contagens = {d: amostra.count(d) for d in [";", ",", "\t", "|"]}
    delim = max(contagens, key=contagens.get)
    return [[c.strip() for c in r] for r in csv.reader(io.StringIO(txt), delimiter=delim)]


def folhas_excel(caminho, folha=None):
    import pandas as pd
    xl = pd.read_excel(caminho, sheet_name=folha if folha else None, header=None, dtype=object)
    if isinstance(xl, dict):
        return [(nome, df.values.tolist()) for nome, df in xl.items()]
    return [(folha, xl.values.tolist())]


def linhas_pdf_tabelas(caminho):
    import pdfplumber
    rows = []
    with pdfplumber.open(caminho) as pdf:
        for page in pdf.pages:
            for t in page.extract_tables() or []:
                rows.extend([[(c or "").replace("\n", " ").strip() for c in r] for r in t])
    return rows


def linhas_pdf_texto(caminho):
    import pdfplumber
    out = []
    with pdfplumber.open(caminho) as pdf:
        for page in pdf.pages:
            out.extend((page.extract_text() or "").splitlines())
    return out


# ------------------------------------------------------------------ cabeçalho
def _match(cell, keys):
    k = chave(cell)
    if not k:
        return None
    for i, key in enumerate(keys):
        if k == key or k.startswith(key + " ") or k.startswith(key) or (" " + key) in (" " + k):
            return i
    return None


def detetar_mapa(rows, max_linhas=60):
    """Procura a linha de cabeçalho e o índice de cada coluna. Devolve dict ou None."""
    melhor = None
    for i, row in enumerate(rows[:max_linhas]):
        cells = ["" if c is None else str(c) for c in row]
        m = {}
        # data
        cand = [(r, j) for j, c in enumerate(cells) if (r := _match(c, DATE_KEYS)) is not None and "valor" not in chave(c)]
        cand_valor = [(99, j) for j, c in enumerate(cells) if chave(c).startswith("data valor")]
        if not cand:
            cand = cand_valor
        if not cand:
            continue
        m["data"] = min(cand)[1]
        usados = {m["data"]} | {j for _, j in cand_valor}
        for nome, keys in (("saldo", SALDO_KEYS), ("debito", DEBIT_KEYS), ("credito", CREDIT_KEYS),
                           ("sinal_col", SIGN_KEYS)):
            cand = [(r, j) for j, c in enumerate(cells) if j not in usados and (r := _match(c, keys)) is not None]
            if cand:
                m[nome] = min(cand)[1]
                usados.add(m[nome])
        cand = [(r, j) for j, c in enumerate(cells)
                if j not in usados and (r := _match(c, AMOUNT_KEYS)) is not None and "saldo" not in chave(c)]
        if cand:
            m["valor"] = min(cand)[1]
            usados.add(m["valor"])
        cand = [(r, j) for j, c in enumerate(cells) if j not in usados and (r := _match(c, DESC_KEYS)) is not None]
        if cand:
            m["descricao"] = min(cand)[1]
        if "descricao" in m and ("valor" in m or "debito" in m or "credito" in m):
            if "valor" in m and ("debito" in m or "credito" in m):
                # "Valor" + "Débito/Crédito" como coluna de sinal
                if "credito" not in m and "sinal_col" not in m:
                    m["sinal_col"] = m.pop("debito")
            m["linha_cabecalho"] = i
            m["_cabecalhos"] = cells
            score = len(m)
            if not melhor or score > melhor[0]:
                melhor = (score, m)
            if score >= 6:
                break
    return melhor[1] if melhor else None


def mapa_por_nomes(rows, mapa):
    """Converte um mapa com nomes de colunas (do config) em índices."""
    i = int(mapa.get("linha_cabecalho", 0))
    cells = [chave(c) for c in rows[i]]
    out = {"linha_cabecalho": i, "_cabecalhos": rows[i]}
    for k in ("data", "descricao", "valor", "debito", "credito", "saldo", "sinal_col"):
        if k in mapa:
            v = mapa[k]
            if isinstance(v, int):
                out[k] = v
            else:
                alvo = chave(v)
                if alvo not in cells:
                    raise SystemExit(f"Coluna '{v}' não encontrada na linha {i}: {rows[i]}")
                out[k] = cells.index(alvo)
    return out


# ------------------------------------------------------------------ linhas -> movimentos
def extrair(rows, mapa, formato_data=None):
    h = mapa["linha_cabecalho"]
    out = []
    g = lambda r, k: (r[mapa[k]] if k in mapa and mapa[k] < len(r) else None)
    for idx, r in enumerate(rows[h + 1:], start=h + 1):
        if not r or all((c is None or str(c).strip() in ("", "nan")) for c in r):
            continue
        d = data_pt(g(r, "data"), formato_data)
        desc = g(r, "descricao")
        desc = "" if desc is None or str(desc) == "nan" else re.sub(r"\s+", " ", str(desc)).strip()
        if d is None:
            # linha de continuação da descrição (comum em PDFs e alguns Excel)
            if out and desc and all(num_pt(g(r, k)) is None for k in ("valor", "debito", "credito")):
                out[-1]["descricao"] = (out[-1]["descricao"] + " " + desc).strip()
            continue
        if RESUMO.match(desc):
            continue
        v = num_pt(g(r, "valor")) if "valor" in mapa else None
        if v is None and ("debito" in mapa or "credito" in mapa):
            deb, cred = num_pt(g(r, "debito")), num_pt(g(r, "credito"))
            if deb is None and cred is None:
                continue
            v = (abs(cred) if cred else 0.0) - (abs(deb) if deb else 0.0)
        if v is None:
            continue
        if "sinal_col" in mapa:
            s = chave(g(r, "sinal_col") or "")
            if s.startswith("d"):
                v = -abs(v)
            elif s.startswith("c"):
                v = abs(v)
        out.append({"data": d, "descricao": desc, "valor": round(v, 2),
                    "saldo": num_pt(g(r, "saldo")) if "saldo" in mapa else None, "linha": idx})
    return out


RX_LINHA_PDF = re.compile(
    r"^(?P<d1>\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?)\s+(?:(?P<d2>\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?)\s+)?"
    r"(?P<desc>.+?)\s+(?P<v>[-−]?\d{1,3}(?:[.\s]\d{3})*,\d{2}-?)(?:\s+(?P<s>[-−]?\d{1,3}(?:[.\s]\d{3})*,\d{2}-?))?\s*$")


def extrair_pdf_texto(linhas, ano=None):
    """Modo de recurso para PDFs sem tabelas. O sinal vem da variação do saldo quando há saldo."""
    out, saldo_ant = [], None
    for idx, ln in enumerate(linhas):
        m = RX_LINHA_PDF.match(ln.strip())
        if not m:
            if out and ln.strip() and not re.search(r"\d,\d{2}", ln) and len(ln.strip()) < 60:
                out[-1]["descricao"] += " " + ln.strip()
            continue
        ds = m.group("d1")
        if ds.count("/") + ds.count("-") + ds.count(".") == 1 and ano:
            ds = f"{ds}/{ano}"
        d = data_pt(ds)
        if not d:
            continue
        v, s = num_pt(m.group("v")), num_pt(m.group("s")) if m.group("s") else None
        if RESUMO.match(m.group("desc")):
            saldo_ant = s if s is not None else v
            continue
        if s is not None and saldo_ant is not None and abs(abs(s - saldo_ant) - abs(v)) < 0.011:
            v = s - saldo_ant
        out.append({"data": d, "descricao": m.group("desc").strip(), "valor": round(v, 2), "saldo": s, "linha": idx})
        if s is not None:
            saldo_ant = s
    return out


PERIODO = re.compile(r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})\s*(?:a|até|ate|-|–)\s*"
                     r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})", re.I)


def periodo_no_topo(rows, ate):
    txt = " ".join(" ".join("" if c is None else str(c) for c in r) for r in rows[:max(ate, 1)])
    m = PERIODO.search(txt)
    if m:
        a, b = data_pt(m.group(1)), data_pt(m.group(2))
        if a and b and a <= b:
            return [a.isoformat(), b.isoformat()]
    return None


def ler_ficheiro(caminho, conta=None):
    """Devolve (movimentos, info)."""
    conta = conta or {}
    p = Path(caminho)
    ext = p.suffix.lower()
    mapa_cfg = conta.get("mapa") or {}
    info = {"ficheiro": str(p), "avisos": []}
    if conta.get("parser"):
        mod_path = Path(conta["_dir"]) / conta["parser"]
        spec = importlib.util.spec_from_file_location("parser_conta", mod_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        movs = []
        for i, r in enumerate(mod.ler(str(p))):
            movs.append({"data": data_pt(r["data"]), "descricao": str(r["descricao"]).strip(),
                         "valor": round(float(r["valor"]), 2), "saldo": r.get("saldo"), "linha": i})
        info["modo"] = f"parser {conta['parser']}"
        return movs, info
    blocos = []
    if ext in (".csv", ".txt", ".tsv"):
        blocos = [("csv", linhas_csv(p))]
    elif ext in (".xlsx", ".xlsm", ".xls"):
        blocos = folhas_excel(p, mapa_cfg.get("folha"))
    elif ext == ".pdf":
        blocos = [("pdf", linhas_pdf_tabelas(p))]
    else:
        raise SystemExit(f"Formato não suportado: {p.name}")
    for nome, rows in blocos:
        if not rows:
            continue
        mapa = mapa_por_nomes(rows, mapa_cfg) if "data" in mapa_cfg else detetar_mapa(rows)
        if mapa:
            movs = extrair(rows, mapa, mapa_cfg.get("formato_data"))
            if movs:
                info["modo"] = f"tabela ({nome})"
                info["cabecalho"] = {k: (mapa["_cabecalhos"][v] if isinstance(v, int) and k != "linha_cabecalho" else v)
                                     for k, v in mapa.items() if not k.startswith("_")}
                info["periodo_detetado"] = periodo_no_topo(rows, mapa["linha_cabecalho"] + 1)
                return movs, info
    if ext == ".pdf":
        linhas = linhas_pdf_texto(p)
        movs = extrair_pdf_texto(linhas, conta.get("ano"))
        info["modo"] = "pdf em modo de texto"
        info["avisos"].append("PDF lido linha a linha: confirma os totais com verificar.py e, se não baterem, "
                              "escreve um parser próprio para este banco.")
        info["periodo_detetado"] = periodo_no_topo([[l] for l in linhas], 15)
        return movs, info
    info["avisos"].append("Não encontrei a linha de cabeçalho. Usa 'mapa' no config para indicar as colunas.")
    return [], info


def continuidade(movs):
    """Confirma, dentro de um ficheiro, que saldo anterior + valor = saldo. Deteta se o ficheiro está
    em ordem crescente ou decrescente. Devolve None se o ficheiro não tiver saldos."""
    com = [m for m in movs if m.get("saldo") is not None]
    if len(com) < 2:
        return None
    def avaliar(seq):
        quebras = [i for i in range(1, len(seq)) if abs(seq[i - 1]["saldo"] + seq[i]["valor"] - seq[i]["saldo"]) > 0.011]
        return quebras, seq
    q_asc, s_asc = avaliar(com)
    q_desc, s_desc = avaliar(list(reversed(com)))
    quebras, seq, ordem = (q_asc, s_asc, "crescente") if len(q_asc) <= len(q_desc) else (q_desc, s_desc, "decrescente")
    return {"ordem": ordem, "saldo_inicial": round(seq[0]["saldo"] - seq[0]["valor"], 2), "saldo_final": seq[-1]["saldo"],
            "quebras": len(quebras),
            "exemplos": [f"{seq[i]['data']} {seq[i]['descricao'][:40]} {seq[i]['valor']:.2f}: esperado "
                         f"{seq[i - 1]['saldo'] + seq[i]['valor']:.2f}, extrato {seq[i]['saldo']:.2f}" for i in quebras[:5]]}


# ------------------------------------------------------------------ comandos
def inspecionar(caminho):
    p = Path(caminho)
    print(f"== {p.name}")
    ext = p.suffix.lower()
    if ext in (".csv", ".txt", ".tsv"):
        rows = linhas_csv(p)
    elif ext in (".xlsx", ".xlsm", ".xls"):
        rows = folhas_excel(p)[0][1]
    else:
        rows = linhas_pdf_tabelas(p) or [[l] for l in linhas_pdf_texto(p)]
    print("-- primeiras linhas")
    for i, r in enumerate(rows[:15]):
        print(f"{i:>3}: {[c for c in r][:10]}")
    movs, info = ler_ficheiro(p)
    print("-- interpretação")
    print(json.dumps({k: v for k, v in info.items() if k != "ficheiro"}, ensure_ascii=False, indent=1, default=str))
    print(f"-- {len(movs)} movimentos; primeiros 5:")
    for m in movs[:5]:
        print(f"   {m['data']}  {m['valor']:>10.2f}  saldo={m['saldo']}  {m['descricao'][:70]}")
    if movs:
        print(f"-- de {min(m['data'] for m in movs)} a {max(m['data'] for m in movs)}; "
              f"entradas {sum(m['valor'] for m in movs if m['valor'] > 0):.2f}; "
              f"saídas {sum(m['valor'] for m in movs if m['valor'] < 0):.2f}")


def fontes_da_conta(conta, base):
    out = []
    for f in conta.get("ficheiros", []):
        spec = {"padrao": f} if isinstance(f, str) else dict(f)
        caminhos = sorted(glob.glob(str(Path(base) / spec["padrao"])))
        if not caminhos:
            print(f"AVISO: nenhum ficheiro para '{spec['padrao']}' (conta {conta['id']})")
        for c in caminhos:
            out.append((c, data_pt(spec.get("desde")), data_pt(spec.get("ate"))))
    return out


def correr(config_path, saida=None):
    cfg = ler_config(config_path)
    base = cfg["_dir"]
    saida = Path(saida or Path(base) / "movimentos.csv")
    linhas, meta = [], {"ficheiros": [], "contas": {}}
    for conta in cfg["contas"]:
        conta = dict(conta, _dir=base)
        por_ficheiro = []
        for fi, (caminho, desde, ate) in enumerate(fontes_da_conta(conta, base)):
            movs, info = ler_ficheiro(caminho, conta)
            if conta.get("sinal") == "invertido":
                for m in movs:
                    m["valor"] = -m["valor"]
            info["continuidade"] = continuidade(movs)
            antes = len(movs)
            movs = [m for m in movs if (not desde or m["data"] >= desde) and (not ate or m["data"] <= ate)]
            info.update(conta=conta["id"], movimentos=len(movs), fora_do_intervalo=antes - len(movs))
            if movs:
                info["de"], info["a"] = str(min(m["data"] for m in movs)), str(max(m["data"] for m in movs))
            meta["ficheiros"].append(info)
            por_ficheiro.append((Path(caminho).name, fi, movs))
        # duplicados entre ficheiros sobrepostos: cada movimento conta o máximo de vezes que aparece num ficheiro
        maximo = Counter()
        for _, _, movs in por_ficheiro:
            c = Counter((m["data"], m["descricao"], m["valor"], m["saldo"]) for m in movs)
            for k, n in c.items():
                maximo[k] = max(maximo[k], n)
        usados, removidos, n_ocorr = Counter(), 0, Counter()
        for nome, fi, movs in por_ficheiro:
            for m in movs:
                k = (m["data"], m["descricao"], m["valor"], m["saldo"])
                if usados[k] >= maximo[k]:
                    removidos += 1
                    continue
                usados[k] += 1
                base_k = (str(m["data"]), m["descricao"], m["valor"])
                n_ocorr[base_k] += 1
                linhas.append({"id": id_movimento(conta["id"], m["data"], m["descricao"], m["valor"], n_ocorr[base_k]),
                               "conta": conta["id"], "data": m["data"].isoformat(), "descricao": m["descricao"],
                               "valor": f"{m['valor']:.2f}",
                               "saldo": "" if m["saldo"] is None else f"{m['saldo']:.2f}",
                               "ficheiro": nome, "ordem": fi * 100000 + m["linha"]})
        n = sum(1 for l in linhas if l["conta"] == conta["id"])
        meta["contas"][conta["id"]] = {"movimentos": n, "duplicados_removidos": removidos}
        if conta["tipo"] == "cartao" and n:
            pos = sum(1 for l in linhas if l["conta"] == conta["id"] and float(l["valor"]) > 0)
            if pos > n / 2:
                meta["contas"][conta["id"]]["aviso"] = ("A maioria dos valores do cartão é positiva: "
                                                        "se as compras aparecem positivas, usa \"sinal\": \"invertido\".")
    j0 = inicio_janela(cfg, max((data_pt(l["data"]) for l in linhas), default=None))
    if j0:
        antes = len(linhas)
        linhas = [l for l in linhas if l["data"] >= j0.isoformat()]
        meta["janela"] = {"inicio": j0.isoformat(), "meses": cfg["janela_meses"], "fora_da_janela": antes - len(linhas)}
        print(f"Janela dos últimos {cfg['janela_meses']} meses: desde {j0:%d/%m/%Y} ({antes - len(linhas)} movimentos mais antigos ficam de fora)")
    linhas.sort(key=lambda l: (l["conta"], l["data"], l["ordem"]))
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS_MOV)
        w.writeheader()
        w.writerows(linhas)
    with open(saida.with_name("movimentos_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1, default=str)
    print(f"{len(linhas)} movimentos escritos em {saida}")
    for c, m in meta["contas"].items():
        extra = f" · {m['duplicados_removidos']} duplicados removidos" if m["duplicados_removidos"] else ""
        print(f"  {c}: {m['movimentos']} movimentos{extra}" + (f"\n  AVISO: {m['aviso']}" if m.get("aviso") else ""))
    for fi in meta["ficheiros"]:
        for a in fi["avisos"]:
            print(f"  AVISO {Path(fi['ficheiro']).name}: {a}")
        if fi.get("movimentos", 0) == 0:
            print(f"  AVISO {Path(fi['ficheiro']).name}: 0 movimentos lidos")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config")
    ap.add_argument("--saida")
    ap.add_argument("--inspecionar", nargs="+")
    a = ap.parse_args()
    if a.inspecionar:
        for c in a.inspecionar:
            inspecionar(c)
    elif a.config:
        correr(a.config, a.saida)
    else:
        ap.print_help()
