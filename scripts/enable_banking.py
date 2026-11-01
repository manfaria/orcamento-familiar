#!/usr/bin/env python3
"""Descarrega movimentos diretamente dos bancos através da API Enable Banking (opcional).

Corre no computador da família: a chave privada nunca deve sair de lá nem ir para o dashboard.
Requisitos: pip install pyjwt cryptography requests

Configuração (variáveis de ambiente ou argumentos):
  EB_APP_ID     Application ID da aplicação criada no Control Panel da Enable Banking
  EB_KEY        caminho do ficheiro .pem com a chave privada dessa aplicação
  EB_REDIRECT   redirect URL registado na aplicação (ex.: https://localhost/retorno)

Comandos:
  python enable_banking.py bancos --pais PT
      lista os bancos disponíveis em Portugal (confirma o nome exato a usar em "ligar")
  python enable_banking.py ligar --banco "Santander Totta" --pais PT --pasta PASTA
      abre a autorização no banco; no fim, cola o endereço para onde o banco te mandou.
      Guarda PASTA/eb_sessoes.json com a sessão e as contas (válida até 180 dias).
  python enable_banking.py descarregar --pasta PASTA [--desde AAAA-MM-DD] [--config config.json]
      descarrega os movimentos lançados de todas as contas ligadas para PASTA/eb_<conta>.csv,
      no formato que ler_extratos.py lê diretamente. Com --config, usa o id da conta do config
      quando a conta tiver "enable_banking": {"uid": "..."}.
  python enable_banking.py estado --pasta PASTA
      mostra as sessões e quantos dias faltam para cada autorização expirar.
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import uuid
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

API = "https://api.enablebanking.com"


def cabecalhos(app_id, chave):
    import jwt
    agora = int(time.time())
    token = jwt.encode({"iss": "enablebanking.com", "aud": "api.enablebanking.com", "iat": agora, "exp": agora + 3600},
                       Path(chave).read_text(), algorithm="RS256", headers={"kid": app_id})
    return {"Authorization": f"Bearer {token}"}


def pedido(metodo, caminho, cred, **kw):
    import requests
    r = requests.request(metodo, API + caminho, headers=cabecalhos(*cred), timeout=60, **kw)
    if r.status_code >= 400:
        raise SystemExit(f"Erro {r.status_code} em {caminho}: {r.text[:500]}")
    return r.json()


def cmd_bancos(a, cred):
    for b in pedido("GET", "/aspsps", cred, params={"country": a.pais})["aspsps"]:
        print(f"{b['name']}  ·  {', '.join(b.get('psu_types', []))}")


def cmd_ligar(a, cred):
    validade = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=a.dias)).isoformat()
    corpo = {"access": {"valid_until": validade}, "aspsp": {"name": a.banco, "country": a.pais},
             "state": str(uuid.uuid4()), "redirect_url": a.redirect, "psu_type": "personal"}
    url = pedido("POST", "/auth", cred, json=corpo)["url"]
    print("1. Abre este endereço e autoriza o acesso no teu banco:\n   " + url)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    retorno = input("2. Cola aqui o endereço completo para onde o banco te mandou no fim: ").strip()
    code = parse_qs(urlparse(retorno).query).get("code", [None])[0]
    if not code:
        raise SystemExit("Não encontrei o parâmetro 'code' nesse endereço.")
    s = pedido("POST", "/sessions", cred, json={"code": code})
    pasta = Path(a.pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    f = pasta / "eb_sessoes.json"
    sessoes = json.loads(f.read_text()) if f.exists() else []
    contas = [{"uid": c["uid"], "nome": c.get("name") or c.get("product") or "",
               "iban_fim": ((c.get("account_id") or {}).get("iban") or "")[-4:]} for c in s.get("accounts", [])]
    sessoes.append({"banco": a.banco, "pais": a.pais, "session_id": s["session_id"],
                    "valido_ate": (s.get("access") or {}).get("valid_until", validade), "contas": contas})
    f.write_text(json.dumps(sessoes, ensure_ascii=False, indent=1))
    print(f"Sessão guardada em {f}. Contas ligadas:")
    for c in contas:
        print(f"  uid={c['uid']}  {c['nome']}  …{c['iban_fim']}")
    print('Põe cada uid no config.json, na conta certa: "enable_banking": {"uid": "..."}')


def linha_mov(t):
    v = float(t["transaction_amount"]["amount"])
    v = -abs(v) if t.get("credit_debit_indicator") == "DBIT" else abs(v)
    partes = []
    for k in ("creditor", "debtor"):
        nome = (t.get(k) or {}).get("name")
        if nome:
            partes.append(nome)
    ri = t.get("remittance_information") or []
    partes += ri if isinstance(ri, list) else [str(ri)]
    if not partes and t.get("note"):
        partes.append(t["note"])
    saldo = (t.get("balance_after_transaction") or {}).get("amount")
    data = t.get("booking_date") or t.get("value_date") or t.get("transaction_date")
    return {"data": data, "descricao": " ".join(dict.fromkeys(p.strip() for p in partes if p and p.strip())),
            "valor": f"{v:.2f}", "saldo": "" if saldo is None else f"{float(saldo):.2f}",
            "referencia": t.get("entry_reference") or t.get("transaction_id") or ""}


def cmd_descarregar(a, cred):
    pasta = Path(a.pasta)
    sessoes = json.loads((pasta / "eb_sessoes.json").read_text())
    mapa = {}
    if a.config:
        cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
        mapa = {c["enable_banking"]["uid"]: c["id"] for c in cfg.get("contas", []) if c.get("enable_banking", {}).get("uid")}
    desde = a.desde or (dt.date.today() - dt.timedelta(days=365)).isoformat()
    for s in sessoes:
        dias = (dt.datetime.fromisoformat(s["valido_ate"].replace("Z", "+00:00")) - dt.datetime.now(dt.timezone.utc)).days
        if dias < 0:
            print(f"AVISO: a autorização de {s['banco']} expirou. Volta a correr 'ligar'.")
            continue
        if dias < 15:
            print(f"AVISO: a autorização de {s['banco']} expira daqui a {dias} dias.")
        for c in s["contas"]:
            linhas, chave = [], None
            while True:
                params = {"date_from": desde, "transaction_status": "BOOK"}
                if chave:
                    params["continuation_key"] = chave
                r = pedido("GET", f"/accounts/{c['uid']}/transactions", cred, params=params)
                linhas += [linha_mov(t) for t in r.get("transactions", [])]
                chave = r.get("continuation_key")
                if not chave:
                    break
            nome = mapa.get(c["uid"], c["uid"])
            destino = pasta / f"eb_{nome}.csv"
            linhas.sort(key=lambda l: l["data"])
            with open(destino, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["data", "descricao", "valor", "saldo", "referencia"])
                w.writeheader()
                w.writerows(linhas)
            print(f"{s['banco']} {c['nome']}: {len(linhas)} movimentos desde {desde} → {destino}")


def cmd_estado(a, cred):
    for s in json.loads((Path(a.pasta) / "eb_sessoes.json").read_text()):
        dias = (dt.datetime.fromisoformat(s["valido_ate"].replace("Z", "+00:00")) - dt.datetime.now(dt.timezone.utc)).days
        print(f"{s['banco']}: {len(s['contas'])} contas · {'expirada' if dias < 0 else f'expira daqui a {dias} dias'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--app-id", default=os.environ.get("EB_APP_ID"))
    ap.add_argument("--chave", default=os.environ.get("EB_KEY"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("bancos"); p.add_argument("--pais", default="PT")
    p = sub.add_parser("ligar"); p.add_argument("--banco", required=True); p.add_argument("--pais", default="PT")
    p.add_argument("--pasta", required=True); p.add_argument("--dias", type=int, default=180)
    p.add_argument("--redirect", default=os.environ.get("EB_REDIRECT", "https://localhost/retorno"))
    p = sub.add_parser("descarregar"); p.add_argument("--pasta", required=True); p.add_argument("--desde"); p.add_argument("--config")
    p = sub.add_parser("estado"); p.add_argument("--pasta", required=True)
    a = ap.parse_args()
    if a.cmd != "estado" and (not a.app_id or not a.chave):
        sys.exit("Indica --app-id e --chave (ou as variáveis EB_APP_ID e EB_KEY).")
    {"bancos": cmd_bancos, "ligar": cmd_ligar, "descarregar": cmd_descarregar, "estado": cmd_estado}[a.cmd](a, (a.app_id, a.chave))
