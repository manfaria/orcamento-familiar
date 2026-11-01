"""Funções partilhadas pelos scripts do Orçamento Familiar.

Formato normalizado de um movimento (movimentos.csv):
    id, conta, data (AAAA-MM-DD), descricao, valor (negativo = saída), saldo, ficheiro, ordem
"""
import calendar
import datetime as dt
import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path

COLS_MOV = ["id", "conta", "data", "descricao", "valor", "saldo", "ficheiro", "ordem"]
COLS_CLASS = COLS_MOV + ["tipo", "categoria", "subcategoria", "ambito", "contribuinte", "nota", "regra"]

TIPOS = {
    "D": "Despesa",
    "R": "Rendimento",
    "T": "Transferência interna",
    "C": "Pagamento de cartão",
    "P": "Poupança e investimento",
    "X": "Extraordinário",
    "I": "Imóvel arrendado",
}

# Cartão refeição em uso misto: categorias que contam como da família (o resto fica pessoal do titular).
REFEICAO_MISTO = {"Supermercado & alimentação": "familia"}


# ---------------------------------------------------------------- texto
def sem_acentos(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c))


def chave(s: str) -> str:
    """Texto simplificado para comparar cabeçalhos: minúsculas, sem acentos nem pontuação."""
    s = sem_acentos(s).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


# ---------------------------------------------------------------- números
def num_pt(v):
    """Converte '1.234,56', '-1 234,56 €', '1234.56', '12,5-', '(12,50)' e números Excel em float.
    Devolve None se não for um número."""
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        if isinstance(v, float) and math.isnan(v):
            return None
        return float(v)
    s = str(v).strip()
    if not s or s.lower() in {"nan", "none", "-", "--"}:
        return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    s = s.replace("EUR", "").replace("€", "").replace(" ", " ").replace(" ", " ").strip()
    if s.endswith("-"):
        neg, s = True, s[:-1].strip()
    if s.startswith("+"):
        s = s[1:].strip()
    if s.startswith("-") or s.startswith("−"):
        neg, s = (not neg), s[1:].strip()
    s = s.replace(" ", "")
    if not re.fullmatch(r"[\d.,]+", s):
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):          # 1.234,56
            s = s.replace(".", "").replace(",", ".")
        else:                                    # 1,234.56
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".") if re.search(r",\d{1,2}$", s) or s.count(",") == 1 else s.replace(",", "")
    elif s.count(".") > 1:
        s = s.replace(".", "")
    elif re.fullmatch(r"\d{1,3}\.\d{3}", s):
        # '1.234' é ambíguo; nos bancos portugueses o ponto é separador de milhares
        s = s.replace(".", "")
    try:
        x = float(s)
    except ValueError:
        return None
    return -x if neg else x


# ---------------------------------------------------------------- datas
_PT_MESES = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6, "jul": 7, "ago": 8,
             "set": 9, "out": 10, "nov": 11, "dez": 12}


def data_pt(v, formato=None):
    """Converte datas portuguesas, ISO ou objetos de data do Excel em datetime.date. None se falhar."""
    if v is None:
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        import pandas as pd
        if isinstance(v, pd.Timestamp):
            return None if pd.isna(v) else v.date()
    except ImportError:
        pass
    if isinstance(v, float) and math.isnan(v):
        return None
    s = str(v).strip()
    if not s:
        return None
    if formato:
        try:
            return dt.datetime.strptime(s, formato).date()
        except ValueError:
            return None
    s = s.split("T")[0].split(" ")[0] if re.match(r"\d{4}-\d{2}-\d{2}", s) else s
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        y, mo, d = map(int, m.groups())
        return _safe(y, mo, d)
    m = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})", s)
    if m:
        d, mo, y = map(int, m.groups())
        if y < 100:
            y += 2000
        return _safe(y, mo, d)
    m = re.fullmatch(r"(\d{1,2})[ ./-]([A-Za-zçÇ]{3})[a-zç]*[ ./-](\d{2,4})", s)
    if m:
        d, mon, y = m.groups()
        mo = _PT_MESES.get(sem_acentos(mon).lower()[:3])
        y = int(y) + (2000 if len(y) == 2 else 0)
        return _safe(y, mo, int(d)) if mo else None
    return None


def _safe(y, mo, d):
    try:
        return dt.date(y, mo, d)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------- ids
def id_movimento(conta, data, descricao, valor, n):
    raw = f"{conta}|{data}|{descricao}|{valor:.2f}|{n}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------- config
def ler_config(caminho):
    p = Path(caminho)
    with open(p, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["_dir"] = str(p.resolve().parent)
    ids = [c["id"] for c in cfg.get("contas", [])]
    if len(ids) != len(set(ids)):
        raise SystemExit("config.json: há contas com o mesmo id.")
    pessoas = {p["id"] for p in cfg.get("pessoas", [])}
    for c in cfg.get("contas", []):
        if c.get("tipo") not in {"conjunta", "pessoal", "cartao", "refeicao"}:
            raise SystemExit(f"config.json: a conta {c['id']} tem de ter tipo conjunta, pessoal, cartao ou refeicao.")
        if c["tipo"] == "refeicao" and c.get("uso") not in {"individual", "familia", "misto"}:
            raise SystemExit(f"config.json: o cartão refeição {c['id']} tem de ter \"uso\": individual, familia ou misto "
                             "(pergunta à família como o usa).")
        for t in c.get("titulares", []):
            if t not in pessoas:
                raise SystemExit(f"config.json: o titular {t} da conta {c['id']} não está em 'pessoas'.")
    return cfg


def guardar_config(cfg, caminho):
    c = {k: v for k, v in cfg.items() if not k.startswith("_")}
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=2)


def conta_por_id(cfg):
    return {c["id"]: c for c in cfg.get("contas", [])}


def ambito_padrao(conta):
    """Contas conjuntas pagam a família; contas pessoais e cartões pagam o titular (se for só um).
    Cartão refeição: com "uso": "familia" paga a família; "individual" e "misto" pagam o titular
    (no misto, o classificador passa para a família as categorias de "ambito_refeicao")."""
    if conta["tipo"] == "conjunta":
        return "familia"
    if conta["tipo"] == "refeicao" and conta.get("uso") == "familia":
        return "familia"
    tit = conta.get("titulares", [])
    return tit[0] if len(tit) == 1 else "familia"


# ---------------------------------------------------------------- períodos
def meses_entre(d0: dt.date, d1: dt.date):
    """Lista de 'AAAA-MM' de d0 a d1 (inclusive)."""
    out, y, m = [], d0.year, d0.month
    while (y, m) <= (d1.year, d1.month):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def meses_cobertos(inicio: dt.date, fim: dt.date) -> float:
    """Meses (com uma casa decimal) entre duas datas, inclusive."""
    dias = (fim - inicio).days + 1
    return round(dias / (365.25 / 12), 1)


def mes_completo(mes: str, inicio: dt.date, fim: dt.date) -> bool:
    y, m = map(int, mes.split("-"))
    d0 = dt.date(y, m, 1)
    d1 = dt.date(y, m, calendar.monthrange(y, m)[1])
    return inicio <= d0 and fim >= d1


def inicio_janela(cfg, data_max):
    """Com "janela_meses": N no config, devolve o primeiro dia da janela dos últimos N meses até data_max."""
    n = cfg.get("janela_meses")
    if not n or data_max is None:
        return None
    y, m = data_max.year, data_max.month - int(n)
    while m <= 0:
        y, m = y - 1, m + 12
    d = min(data_max.day, calendar.monthrange(y, m)[1])
    return dt.date(y, m, d) + dt.timedelta(days=1)


def cobertura_contas(cfg, mov):
    """Devolve {conta: (inicio, fim, meses)} a partir do config (inicio/fim) ou dos movimentos.

    'mov' é um DataFrame com colunas conta e data (texto AAAA-MM-DD)."""
    out = {}
    j0 = inicio_janela(cfg, data_pt(mov.data.max()) if len(mov) else None)
    for c in cfg.get("contas", []):
        sub = mov[mov.conta == c["id"]]
        ini = data_pt(c.get("inicio")) or (data_pt(sub.data.min()) if len(sub) else None)
        fim = data_pt(c.get("fim")) or (data_pt(sub.data.max()) if len(sub) else None)
        if ini and j0 and ini < j0:
            ini = j0
            c = {k: v for k, v in c.items() if k != "meses"}
        if ini and fim:
            meses = float(c.get("meses") or meses_cobertos(ini, fim))
            out[c["id"]] = (ini, fim, meses)
    return out
