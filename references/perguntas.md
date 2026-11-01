# Perfil da família: o que definir antes de classificar

Cada família organiza o dinheiro à sua maneira. Estas perguntas decidem como os movimentos são lidos e o que o dashboard mostra. Faz só as que se aplicam, em rondas curtas (até 4 perguntas por ronda), e salta o que os ficheiros já respondem. Aceita sempre "não sei" e "não quero dizer". Regista cada resposta em `decisoes.md`, com data, e passa-a para o config ou para `regras.csv` como indicado.

## Ronda 1. Pessoas e contas
1. **Quem faz parte do orçamento:** as pessoas que contribuem com dinheiro. Os filhos só entram como categoria de despesa. → `pessoas`.
2. **De quem é cada conta e cada ficheiro:** conjunta, pessoal de alguém, cartão de crédito de alguém (e de que conta é pago), cartão refeição. → `contas`.
3. **Nomes nas transferências:** como aparece o nome de cada pessoa e de quem ajuda (por exemplo "TRF. DE ANA P COSTA"). → `nomes_banco`.
4. **Contas que não estão nos extratos:** Revolut, Wise, poupança, corretoras, cripto. São poupança, investimento ou contas de gastos? Se forem de gastos, pede também esses extratos.

## Ronda 2. Como se paga a vida da família
1. **Como entra o dinheiro para as despesas comuns:** transferências mensais para a conjunta, depósitos em numerário, ou cada um paga umas coisas.
2. **Despesas da família pagas de contas pessoais:** renda, luz, supermercado, creche… Quais e por quem. → regras com `ambito: familia` ou `ambito_por_categoria`.
3. **Ajudas de fora:** pais, avós ou outros que transferem dinheiro, e para que conta. → `contribuidores_externos`.
4. **Despesas pagas por outros:** avós que pagam a escola ou as atividades, empresa que paga o telemóvel. → `fora_dos_extratos`, se a família quiser ver o custo real.

## Ronda 3. Cartão refeição e outros benefícios
1. **Cartão refeição:** alguém recebe o subsídio de refeição em cartão (Edenred, Pluxee, Coverflex ou outro)? Se sim, **como é usado:**
   - **Individual** (almoços de trabalho, cafés): é gasto pessoal de quem o recebe. O extrato é opcional; sem extrato, regista só o valor mensal, se a família quiser, em `fora_dos_extratos` com `"ambito": "<pessoa>"`.
   - **Despesas da família** (supermercado da casa): pede o extrato do cartão. → conta `"tipo": "refeicao", "uso": "familia"`.
   - **Misto** (almoços e supermercado): pede o extrato. → `"uso": "misto"`; o supermercado conta como da família e o resto como pessoal. Confirma com a família e ajusta `ambito_refeicao` se for diferente (restaurantes em família, por exemplo).
   - **Extrato:** muitos emissores mostram os movimentos na app ou no site. Pede uma exportação (CSV, Excel ou PDF) dos mesmos meses dos outros extratos. Se não houver, aceita capturas de ecrã ou o PDF do resumo, e lê os movimentos a partir daí.
   - **Sem extrato possível** num uso familiar ou misto: pede o valor mensal carregado e quanto vai, em média, para a família. → `fora_dos_extratos` com `ambito`, e `extra_mensal` na linha do orçamento do supermercado. Diz no resumo que esta parte é indicada pela família, não vem dos extratos.
   - **Porque importa:** sem o cartão, o supermercado da família parece mais barato do que é e a contribuição de quem tem o cartão parece menor.
2. **Outros benefícios da empresa** que pagam despesas da família: cheque-creche ou cheque-educação, seguro de saúde, planos flexíveis (uma carteira com vários benefícios trata-se como o cartão refeição, com `uso` por categoria), carro ou cartão de combustível da empresa, telemóvel. Só interessam os que substituem despesas que a família teria. → `fora_dos_extratos`, com nota.

## Ronda 4. Situações que mudam as contas
Pergunta só pelas que façam sentido para esta família (o extrato costuma dar pistas).
1. **Casa:** renda ou crédito à habitação? A prestação é da casa onde vivem? → `Casa & contas`.
2. **Imóveis arrendados a terceiros:** rendas recebidas, prestação, condomínio, IMI e seguro desse imóvel. → regras com tipo `I`, `categoria` = nome do imóvel (por exemplo "T1 Almada"), `subcategoria` = renda recebida, prestação, condomínio, IMI… O dashboard mostra o resultado de cada imóvel e não o mistura com as despesas da família. Segunda casa ou casa de férias usadas pela família são despesa normal.
3. **Filhos de relações anteriores ou pais separados:** pensão de alimentos paga (despesa, `Educação & filhos` → `Pensão de alimentos`) ou recebida (rendimento). Despesas dos filhos divididas com o outro progenitor: o que ele devolve desconta na categoria (regra com o mesmo `categoria` e valor positivo).
4. **Pessoas a cargo fora de casa:** pais idosos ajudados todos os meses, filhos a estudar fora (renda, mesada). São despesa da família ou de uma pessoa? Cria uma categoria própria se pesar (por exemplo "Apoio aos pais").
5. **Trabalho independente ou empresa própria:** a atividade tem conta própria? Se tiver, fica fora (não se pede). Se estiver misturada: rendimentos em `Rendimentos` → `Trabalho independente`; Segurança Social e pagamentos por conta de IRS em `Impostos & taxas` (pessoal); IVA entregue e custos da atividade como tipo `T`, categoria `Atividade profissional` (dinheiro do negócio, fora das despesas).
6. **Despesas de trabalho reembolsadas pela empresa** (viagens, refeições com clientes pagas do bolso): a saída e o reembolso ficam como tipo `T`, categoria `Despesas de trabalho (reembolsadas)`. Sem isto, a pessoa parece gastar e ganhar mais do que realmente.
7. **Adiantamentos e contas a meias com amigos ou familiares** (viagens em grupo, jantares, compras por outra pessoa): quando o dinheiro volta, a saída e a devolução ficam como tipo `T`, categoria `Adiantamentos (reembolsados)`. O `analisar.py` lista em `adiantamentos` as saídas que voltaram com o mesmo valor até 90 dias depois: confirma cada par com a família. Se só voltou uma parte (a parte de cada um num jantar), a devolução desconta na categoria da despesa.
8. **Rendimentos irregulares:** subsídios de férias e de Natal pagos à parte ou em duodécimos, prémios anuais, comissões. Entram como rendimento; diz no resumo em que meses chegam, porque costumam pagar as despesas anuais.
9. **Mudanças de vida no período:** bebé, mudança de casa, carro novo ou vendido, desemprego, licença parental, entrada na creche. Explicam picos e quebras. Pergunta se a média de alguma categoria deve contar só a partir da mudança (regras com `data_de`, ou tipo `X` para o que ficou para trás).
10. **Compras e vendas grandes:** carro, obras, entrada de uma casa, venda de um bem. → tipo `X` (extraordinário), fora das médias mas visível. Se a compra foi paga com a venda de investimentos, as duas ficam como `X` ou `P`.
11. **Investimentos e moeda estrangeira:** contas multimoeda, cripto, ações da empresa (planos de ações para trabalhadores). Conversões e compras são poupança (`P`); vendas usadas para despesas grandes são extraordinário (`X`).
12. **Numerário:** levantam dinheiro com regularidade? Para quê (mercado, mesadas, empregada)? Se a família souber, cria regras para os levantamentos dessa finalidade; se não, fica em `Numerário` e sugere-se registar.
13. **Animais, desporto dos filhos, igreja e donativos, explicações:** categorias próprias quando pesam.

## Ronda 5. O que o dashboard mostra
1. **Privacidade dentro da família:** o dashboard vai ser visto por todos? Cada pessoa quer que os outros vejam os seus gastos pessoais em detalhe? → `"pessoal"` no config:
   - `"detalhe"` (por omissão): tudo visível;
   - `"categorias"`: os gastos pessoais aparecem por categoria, sem descrições;
   - `"total"`: só o total pessoal de cada pessoa.
2. **Divisão justa:** querem ver uma proposta? A meias ou proporcional ao rendimento? Se proporcional, rendimento líquido mensal de cada pessoa (inclui o cartão refeição?). → `divisao`, `rendimentos`.
3. **Orçamento planeado:** têm um (ficheiro, foto, escrito)? → passo 5.
4. **Janela:** sempre os últimos 12 meses, ou o ano civil? → `janela_meses`.
5. **Lembrete mensal:** querem? → passo 9.

## Depois das respostas
- Escreve o `config.json` e as regras da família no topo de `regras.csv`.
- Se uma resposta pedir um extrato que ainda não tens (cartão refeição, conta de gastos fora dos extratos), pede-o antes de classificar. Sem ele, diz no resumo o que fica de fora.
- Reflete as respostas no resumo final: o que a família indicou e não vem dos extratos aparece sempre identificado como tal.
