#!/usr/bin/env python3
"""Gera o contexto do orçamento para guardar num projeto do assistente (por exemplo, um projeto do Claude).

Uso:
  python contexto_projeto.py --config orcamento-familiar/config.json

Lê config.json, estado.json, analise.json, movimentos_classificados.csv e decisoes.md da pasta de trabalho e escreve:
  contexto_projeto.md     o documento a guardar no projeto: onde está cada coisa, contas, como se calculam os números,
                          médias por categoria, orçamento vs real, contribuições, evolução mensal, categorias em uso,
                          decisões da família, como fazer uma alteração e o que está em aberto
  instrucoes_projeto.txt  o texto para a família colar nas instruções do projeto

Corre depois de construir_dashboard.py, sempre que alguma coisa mude (extratos novos, regras, decisões).
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import TIPOS, cobertura_contas, conta_por_id, ler_config  # noqa: E402

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
NOME_DOC = "contexto-orcamento-familiar.md"


def eur(v, casas=0):
    s = f"{abs(v):,.{casas}f}".replace(",", " ").replace(".", ",")
    return ("−" if v < 0 else "") + s + " €"


def mes_pt(m):
    y, mm = m.split("-")
    return f"{MESES[int(mm) - 1]}/{y[2:]}"


def ler_json(p):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main(config_path):
    cfg = ler_config(config_path)
    base = Path(cfg["_dir"])
    contas = conta_por_id(cfg)
    nomes = {p["id"]: p.get("nome", p["id"]) for p in cfg.get("pessoas", [])}
    for e in cfg.get("contribuidores_externos", []):
        nomes[e["id"]] = e.get("nome", e["id"])
    nomes["familia"] = "Família"
    A = ler_json(base / "analise.json")
    estado = ler_json(base / "estado.json")
    if not A or not (base / "movimentos_classificados.csv").exists():
        raise SystemExit("Faltam analise.json ou movimentos_classificados.csv: corre primeiro classificar.py e analisar.py.")
    df = pd.read_csv(base / "movimentos_classificados.csv", keep_default_na=False, dtype={"id": str, "conta": str, "data": str})
    df["valor"] = df.valor.astype(float)
    df["mes"] = df.data.str[:7]
    cob = cobertura_contas(cfg, df)
    meses_conta = {c: v[2] for c, v in cob.items()}
    D = df[df.tipo == "D"].copy()
    D["mensal"] = -D.valor / D.conta.map(meses_conta)

    # caminho como a família o vê (por exemplo C:\\Users\\...\\orcamento-familiar), que pode diferir de onde os scripts correm
    pasta = cfg.get("pasta_familia") or str(base)
    url = cfg.get("dashboard_url") or estado.get("dashboard_url") or "(ainda não publicado)"
    hoje = dt.date.today().strftime("%d/%m/%Y")
    L = []
    w = L.append
    w("# Orçamento familiar: contexto do projeto")
    w("")
    w(f"Gerado pela skill Orçamento Familiar a {hoje}. Lê este documento antes de responder a perguntas sobre o orçamento "
      "ou de alterar alguma coisa. Os números vêm dos extratos; se diferirem do dashboard, vale o dashboard.")
    w("")
    w("## Onde está cada coisa")
    w(f"- **Dashboard:** {url}. Atualiza sempre este mesmo link.")
    w(f"- **Pasta de trabalho:** `{pasta}` (config.json, regras.csv, decisoes.md, movimentos_classificados.csv, analise.json). "
      "É a fonte de verdade: qualquer alteração faz-se aqui e só depois se publica.")
    padroes = sorted({(f if isinstance(f, str) else f.get("padrao", "")) for c in cfg.get("contas", []) for f in c.get("ficheiros", [])})
    if padroes:
        w(f"- **Extratos:** {', '.join('`' + p + '`' for p in padroes if p)} (relativos à pasta de trabalho).")
    w("- **Movimentos classificados:** `movimentos_classificados.csv` (data, conta, descrição, valor, tipo, categoria, "
      "subcategoria, âmbito, contribuinte, nota). Para perguntas que este documento não responde, lê esse ficheiro.")
    w("")
    w("## Pessoas e contas")
    w("Pessoas: " + ", ".join(f"{nomes[p['id']]} (`{p['id']}`)" for p in cfg.get("pessoas", [])) + ".")
    if cfg.get("contribuidores_externos"):
        w("Ajudas de fora: " + ", ".join(e.get("nome", e["id"]) for e in cfg["contribuidores_externos"]) + ".")
    w("")
    w("| Conta | Tipo | Titular | Período | Meses na média |")
    w("|---|---|---|---|---|")
    for cid, c in contas.items():
        ini, fim, m = cob.get(cid, (None, None, 0))
        tipo = c["tipo"] + (f" ({c.get('uso')})" if c["tipo"] == "refeicao" else "")
        tit = ", ".join(nomes.get(t, t) for t in c.get("titulares", [])) or "–"
        per = f"{ini:%d/%m/%Y} a {fim:%d/%m/%Y}" if ini else "–"
        meses = f"{m:.1f}".rstrip("0").rstrip(".").replace(".", ",")
        w(f"| {c.get('nome', cid)} (`{cid}`) | {tipo} | {tit} | {per} | {meses} |")
    w("")
    w("Tipos de movimento: " + " · ".join(f"{k} {v.lower()}" for k, v in TIPOS.items()) +
      ". Âmbito: `familia` (despesa da família, paga por qualquer conta) ou o id de uma pessoa (gasto pessoal).")
    w("")
    w("## Como se calculam os números")
    w("- **Média mensal:** cada despesa é dividida pelos meses que a sua conta cobre e somada. Nunca dividas um total por 12 sem ter isto em conta.")
    w("- **Fica fora das despesas:** transferências entre contas, pagamentos do cartão de crédito, poupança, extraordinários, "
      "imóveis arrendados e adiantamentos reembolsados.")
    w("- **Despesas da família pagas de contas pessoais** contam na família e como contribuição de quem pagou.")
    fe = cfg.get("fora_dos_extratos", [])
    if fe:
        w("- **Fora dos extratos (indicado pela família, não entra nas médias):** " +
          "; ".join(f"{f['nome']} {eur(f.get('valor_mensal', 0))}/mês" for f in fe) + ".")
    j = A.get("janela_comum", [])
    if j:
        w(f"- **Contribuições:** calculadas na janela em que todas as contas têm meses completos ({mes_pt(j[0])} a {mes_pt(j[-1])}).")
    w("")
    med = A.get("medias", {})
    w("## Médias mensais (despesa corrente)")
    partes = " + ".join(f"{nomes.get(k, k)} {eur(v)}" for k, v in med.items() if k != "total")
    w(f"**Total: {eur(med.get('total', 0))}/mês** = {partes}.")
    w("")
    modo = cfg.get("pessoal", "detalhe")
    for amb in ["familia"] + [p["id"] for p in cfg.get("pessoas", [])]:
        g = D[D.ambito == amb]
        if not len(g):
            continue
        if modo == "total" and amb != "familia":
            continue  # privacidade dentro da família: só o total pessoal (já indicado acima)
        w(f"### {nomes.get(amb, amb)} ({eur(g.mensal.sum())}/mês)")
        w("| Categoria | €/mês | Principais subcategorias |")
        w("|---|---|---|")
        for cat, v in g.groupby("categoria").mensal.sum().sort_values(ascending=False).items():
            subs = g[g.categoria == cat].groupby("subcategoria").mensal.sum().sort_values(ascending=False)
            txt = "; ".join(f"{s} {eur(x)}" for s, x in subs.items() if s and abs(x) >= 5)
            w(f"| {cat} | {eur(v)} | {txt} |")
        w("")
    orc = A.get("orcamento", [])
    if orc:
        w("## Orçamento planeado vs real (média/mês)")
        w("| Linha | Planeado | Real | Diferença |")
        w("|---|---|---|---|")
        for o in orc:
            w(f"| {o['linha']} | {eur(o['planeado'])} | {eur(o['real'])} | {eur(o['diferenca'])} |")
        w(f"| **Total** | **{eur(sum(o['planeado'] for o in orc))}** | **{eur(sum(o['real'] for o in orc))}** | |")
        w("")
    c = A.get("contribuicoes", {})
    if c.get("por_pessoa"):
        w(f"## Contribuições para a família (média/mês, {c.get('meses')} meses)")
        tot = max(c.get("total", 0), 1)
        for p, v in c["por_pessoa"].items():
            extra = "" if v.get("externo") else f" ({eur(v['para_conjunta'])} para a conjunta + {eur(v['pago_diretamente'])} pagos diretamente)"
            w(f"- {nomes.get(p, p)}: {eur(v['total'])}, {v['total'] / tot:.0%}{extra}")
        w(f"- Total {eur(c.get('total', 0))} contra uma despesa da família de {eur(c.get('despesa_familia', 0))} "
          f"(saldo {eur(c.get('saldo', 0))}/mês).")
        w("")
    fam = D[D.ambito == "familia"].groupby("mes").valor.sum().sort_index()
    if len(fam):
        w("## Evolução da despesa da família (total por mês)")
        w(" · ".join(f"{mes_pt(m)} {eur(-v)}" for m, v in fam.items()) +
          ". Os meses nas pontas e os meses em que falta alguma conta estão incompletos.")
        w("")
    w("## Categorias em uso")
    w("Usa estas categorias e subcategorias. Uma nova só com o acordo da família.")
    for t in ["D", "R", "T", "P", "X", "I", "C"]:
        g = df[df.tipo == t]
        if modo == "total" and t == "D":
            g = g[g.ambito == "familia"]
        if not len(g):
            continue
        w(f"- **{t} {TIPOS[t].lower()}:**")
        for cat, gg in g.groupby("categoria"):
            subs = sorted({s for s in gg.subcategoria if s})
            w(f"  - {cat}" + (": " + " · ".join(subs) if subs else ""))
    w("")
    dec = base / "decisoes.md"
    if dec.exists():
        w("## Decisões da família")
        w("Copiadas de `decisoes.md`. Seguem-se em todas as classificações.")
        w("")
        for linha in dec.read_text(encoding="utf-8").splitlines():
            w(linha.replace("# ", "### ", 1) if linha.startswith("# ") else linha)
        w("")
    w("## Como fazer uma alteração (classificar uma despesa, mudar uma regra, acrescentar algo)")
    w("1. Confirma que tens acesso à pasta de trabalho. Se não tiveres, pede-a antes de mudar alguma coisa: "
      "uma alteração que não fique na pasta perde-se na atualização seguinte.")
    w("2. Encontra o movimento em `movimentos_classificados.csv` (data, conta, valor). Nas dúvidas, pergunta.")
    w("3. Regista a decisão: uma regra no topo de `regras.csv` (padrão que se repete) ou pelo `id` do movimento "
      "(caso pontual), e uma linha datada em `decisoes.md`. Valores fora dos extratos vão para `fora_dos_extratos` no config.")
    w("4. Corre `classificar.py`, `analisar.py` e `construir_dashboard.py`, sem esconder a saída.")
    w("5. Verifica o dashboard (totais, erros, botão do olho) e publica-o no mesmo link.")
    w("6. Corre `contexto_projeto.py` e substitui este documento no projeto pelo `contexto_projeto.md` novo.")
    w("")
    w("## Em aberto")
    pi = A.get("por_identificar", {})
    w(f"- Por identificar: {pi.get('movimentos', 0)} movimentos ({eur(pi.get('por_mes', 0))}/mês).")
    if A.get("adiantamentos"):
        w(f"- Possíveis adiantamentos por confirmar: {len(A['adiantamentos'])}.")
    for k, cc in contas.items():
        ini, fim, m = cob.get(k, (None, None, 0))
        if fim:
            w(f"- {cc.get('nome', k)}: extratos até {fim:%d/%m/%Y}.")
    (base / "contexto_projeto.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    instr = f"""Este projeto é o orçamento familiar da família, feito com a skill Orçamento Familiar.

No início de cada conversa sobre o orçamento, lê o documento {NOME_DOC} do projeto antes de responder ou alterar alguma coisa.

Regras:
- Responde em português europeu.
- Nunca inventes valores. Tudo vem dos extratos ou da família. Nas dúvidas, pergunta antes de classificar.
- Usa as categorias e subcategorias em uso. Uma nova só com o nosso acordo.
- A fonte de verdade é a pasta de trabalho {pasta}. Se não tiveres acesso a ela, avisa antes de alterar alguma coisa.
- Qualquer alteração (classificar uma despesa, mudar uma regra, acrescentar algo ao dashboard) segue os passos do documento: registar em regras.csv e decisoes.md, correr os scripts, verificar e publicar no mesmo link ({url}).
- No fim de qualquer alteração, na mesma conversa, corre contexto_projeto.py e substitui o documento {NOME_DOC} no projeto pela versão nova. Depois diz numa linha o que mudou.
- Se uma conversa não chegar ao fim de uma alteração, regista em decisoes.md o que ficou por fazer.
"""
    (base / "instrucoes_projeto.txt").write_text(instr, encoding="utf-8")
    soma = {k: round(D[D.ambito == k].mensal.sum(), 2) for k in med if k != "total"}
    difs = {k: (soma.get(k, 0), v) for k, v in med.items() if k != "total" and abs(soma.get(k, 0) - v) > 0.05}
    if difs:
        print("Aviso: as médias não batem com analise.json (corre analisar.py de novo):", difs)
    print(f"Escrito {base / 'contexto_projeto.md'} ({len(L)} linhas) e {base / 'instrucoes_projeto.txt'}.")
    print(f"Guarda contexto_projeto.md no projeto com o nome {NOME_DOC}.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    main(ap.parse_args().config)
