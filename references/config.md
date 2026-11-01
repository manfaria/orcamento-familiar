# Formato do config.json

O `config.json` vive na pasta de trabalho e guarda tudo o que a família decidiu. Os campos marcados como opcionais podem faltar.

```json
{
  "familia": "Família Costa",
  "pessoas": [
    {"id": "ana", "nome": "Ana", "nomes_banco": ["Ana Paula Costa", "Ana P Costa"]},
    {"id": "rui", "nome": "Rui", "nomes_banco": ["Rui Miguel Costa"]}
  ],
  "contribuidores_externos": [
    {"id": "mae-rui", "nome": "Mãe do Rui", "nomes_banco": ["Maria Fernanda Costa"]}
  ],
  "contas": [
    {"id": "conjunta", "nome": "Conta conjunta", "banco": "ActivoBank", "tipo": "conjunta", "titulares": ["ana", "rui"],
     "ficheiros": ["Extratos/activo_*.xlsx"], "inicio": "2025-10-01", "fim": "2026-09-30"},
    {"id": "rui", "nome": "Conta do Rui", "banco": "Santander", "tipo": "pessoal", "titulares": ["rui"],
     "ficheiros": [{"padrao": "Extratos/santander_rui*.csv", "ate": "2026-09-30"},
                   {"padrao": "eb/eb_rui.csv", "desde": "2026-10-01"}],
     "enable_banking": {"uid": "a1b2c3"}},
    {"id": "rui-cartao", "nome": "Cartão do Rui", "banco": "Wizink", "tipo": "cartao", "titulares": ["rui"],
     "pago_por": "rui", "ficheiros": ["Extratos/wizink_*.pdf"], "sinal": "invertido"},
    {"id": "ana", "nome": "Conta da Ana", "banco": "CGD", "tipo": "pessoal", "titulares": ["ana"],
     "ficheiros": ["Extratos/cgd_ana.xlsx"],
     "mapa": {"linha_cabecalho": 6, "data": "Data mov.", "descricao": "Descritivo", "debito": "Débito",
              "credito": "Crédito", "saldo": "Saldo contabilístico", "formato_data": "%d-%m-%Y"}},
    {"id": "rui-refeicao", "nome": "Cartão refeição do Rui", "banco": "Edenred", "tipo": "refeicao", "titulares": ["rui"],
     "uso": "misto", "ficheiros": ["Extratos/refeicao_rui.csv"]}
  ],
  "ambito_por_categoria": {"Supermercado & alimentação": "familia"},
  "rendimentos": {"ana": 1900, "rui": 2400},
  "divisao": {"metodo": "proporcional"},
  "orcamento": [
    {"linha": "Casa", "valor": 1050, "categorias": ["Casa & contas"]},
    {"linha": "Supermercado", "valor": 450, "categorias": ["Supermercado & alimentação"], "extra_mensal": 160,
     "nota": "Inclui 160 € do cartão refeição da Ana, que não aparece nos extratos"},
    {"linha": "Carro", "valor": 150, "categorias": ["Transportes", "Seguros"], "subcategorias": [],
     "ambito": "familia"}
  ],
  "orcamento_proposto": false,
  "fora_dos_extratos": [{"nome": "Cheque-creche", "pessoa": "ana", "valor_mensal": 120, "ambito": "familia"}],
  "pessoal": "detalhe",
  "sugestoes": [{"titulo": "Spotify pago duas vezes", "texto": "…", "poupanca_mensal": 10.99}],
  "notas_categorias": {"Casa & contas": "Inclui a renda paga pela Ana da conta dela."},
  "notas_movimentos": {"ffaf5a64810e": "Fisioterapia da Ana (confirmado a 01/11)"},
  "nota_contribuicoes": "",
  "nota_extraordinarios": ""
}
```

## Pessoas e contribuidores
- `id`: curto, sem espaços (usado nas regras e no âmbito). `nome`: como aparece no dashboard.
- `nomes_banco`: como o nome aparece nas descrições das transferências. Uma entrada na conta conjunta com um destes nomes conta como contribuição dessa pessoa; uma saída da conjunta para ela desconta.
- `contribuidores_externos`: quem ajuda de fora (pais, avós). As entradas deles na conjunta contam como contribuição externa; noutras contas contam como rendimento ("Ajuda de …").

## Contas
- `tipo`: `conjunta` (paga a família), `pessoal` (de uma pessoa), `cartao` (cartão de crédito) ou `refeicao` (cartão refeição ou carteira de benefícios da empresa).
- `titulares`: ids das pessoas. Numa conta pessoal, o titular é quem "paga diretamente" quando uma despesa é da família.
- `pago_por`: num cartão, o id da conta de onde sai o pagamento (para emparelhar e não contar duas vezes).
- `ficheiros`: padrões glob relativos à pasta do config. Podem ser objetos com `desde`/`ate` para separar períodos (por exemplo, extratos manuais até setembro e API a partir de outubro).
- `inicio`/`fim`: período que o extrato cobre (do cabeçalho do extrato). Sem eles, usa o primeiro e o último movimento, o que pode encurtar a média. Também se pode fixar `meses` diretamente.
- `sinal`: `"invertido"` quando as compras aparecem como valores positivos.
- `mapa`: força a leitura das colunas quando a deteção automática falha. Os nomes das colunas são comparados sem acentos nem maiúsculas. `linha_cabecalho` conta a partir de 0. Outras chaves: `valor`, `sinal_col` (coluna D/C), `folha` (Excel).
- `parser`: caminho de um módulo Python próprio com `ler(caminho)` que devolve uma lista de `{data, descricao, valor, saldo}`.
- `ano`: para PDFs com datas sem ano.

## Cartão refeição
- `uso` (obrigatório em `tipo: refeicao`):
  - `individual`: as compras são gasto pessoal do titular;
  - `familia`: as compras são despesa da família e contribuição do titular;
  - `misto`: as categorias de `ambito_refeicao` são da família e o resto é pessoal.
- `ambito_refeicao`: só no uso misto. Por omissão `{"Supermercado & alimentação": "familia"}`. Exemplo para incluir as refeições em família: `{"Supermercado & alimentação": "familia", "Restauração": "familia"}`. Uma regra com `ambito` explícito tem prioridade.
- Os carregamentos são rendimento do titular (`Rendimentos` → `Cartão refeição`) e entram na estimativa do rendimento para a divisão proporcional.
- O cartão não entra nos pares de transferências (é carregado pelo empregador, não por contas da família).
- Sem extrato: não cries a conta. Usa `fora_dos_extratos` com `ambito` e, se o uso for familiar, `extra_mensal` na linha do orçamento.

## Janela
- `janela_meses`: por exemplo 12. O dashboard usa só os últimos N meses até ao movimento mais recente, e as médias de cada conta contam a partir do início da janela. Recomendado a partir da primeira atualização mensal, para as médias refletirem o último ano.

## Estado e link
- `dashboard_url`: link do dashboard publicado. As atualizações publicam sempre no mesmo link.
- O `estado.json` (escrito pelo `construir_dashboard.py`) guarda a data da última atualização e até quando vai cada conta. Não se edita à mão.

## Fora dos extratos
- `fora_dos_extratos`: lista de `{"nome", "pessoa", "valor_mensal", "ambito"}` com o que a família indicou e não passa pelos extratos (cartão refeição sem extrato, cheque-creche, seguro de saúde da empresa, despesas pagas pelos avós). `ambito`: `familia` (por omissão) ou o id de uma pessoa. Aparece num cartão próprio e não entra nas médias.

## Privacidade dentro da família
- `pessoal`: `"detalhe"` (por omissão) mostra tudo; `"categorias"` esconde as descrições dos gastos pessoais; `"total"` mostra só o total pessoal de cada pessoa. Os custos fixos e subscrições pessoais também deixam de aparecer. Afeta só o dashboard: os ficheiros de trabalho continuam completos.

## Âmbito
- `ambito_por_categoria`: categorias que contam sempre como da família, mesmo pagas de contas pessoais (útil quando não há conta conjunta). Uma regra com `ambito` explícito tem prioridade.

## Orçamento
- `linha`, `valor` (por mês), `categorias`, `subcategorias` (opcional), `ambito` (`familia` por omissão; `todos` junta família e pessoal).
- `extra_mensal`: soma ao real um valor pago fora dos extratos (indicado pelo utilizador).
- `orcamento_proposto: true` quando foi a skill a propor o orçamento.
