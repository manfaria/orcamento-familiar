---
name: orcamento-familiar
description: Cria e atualiza o dashboard "Orçamento Familiar" a partir de extratos bancários portugueses (CSV, Excel ou PDF). Pergunta como a família organiza as contas, categoriza as despesas, identifica movimentos desconhecidos, compara com o orçamento planeado, calcula quanto cada pessoa contribui e sugere poupanças. Usar quando alguém quiser analisar os gastos da família, fazer ou rever um orçamento familiar, perceber quanto gasta por mês a partir dos extratos, ou atualizar um dashboard Orçamento Familiar com extratos novos.
---

# Orçamento Familiar

Transforma os extratos bancários de uma família num dashboard com a despesa média mensal por categoria, a evolução mês a mês, o orçamento planeado contra o real, a contribuição de cada pessoa, uma proposta de divisão justa e sugestões de poupança. O trabalho é uma conversa: a skill propõe, a família confirma.

## Princípios (não negociáveis)

1. **Nunca inventar valores.** Todos os números vêm dos extratos ou do que o utilizador disser. Se falta informação, pergunta. Não estimes nem preenchas buracos.
2. **Perguntar nas dúvidas.** Nunca adivinhes o que é um movimento, de quem é uma conta ou se uma despesa é da família. Pergunta em lotes curtos e com contexto.
3. **Não contar duas vezes.** Transferências entre contas da família, pagamentos do cartão de crédito e idas e voltas de dinheiro não são despesa nem rendimento.
4. **Cada conta é dividida pelos meses que o seu extrato cobre.** Uma conta com 9 meses de extrato divide por 9, não por 12.
5. **Privacidade.** Extratos são dados muito sensíveis. Trabalha só nesta sessão e não envies dados para outros serviços. A pesquisa na web é só para nomes de empresas, nunca nomes de pessoas. O dashboard sai privado. Antes de alguém partilhar um screenshot, lembra o botão do olho.
6. **Português europeu e sem aconselhamento financeiro.** As sugestões baseiam-se nos movimentos. Não recomendes produtos financeiros, investimentos nem marcas.

## Como explicar ao utilizador

Quem usa esta skill não é necessariamente técnico. Explica sempre o que vais fazer e porquê, em linguagem simples. Não fales em scripts, CSV, regex ou JSON: fala em "ficheiros", "regras", "categorias" e "dashboard". Os detalhes técnicos ficam para quem perguntar.

**No início**, antes de pedir seja o que for, apresenta o processo numa mensagem curta, adaptada a este modelo:

> Vou ajudar-vos a montar o vosso Orçamento Familiar a partir dos extratos bancários. Funciona assim:
> 1. Envias-me os extratos (ou dizes-me em que pasta estão).
> 2. Faço-te umas perguntas sobre as contas: de quem é cada uma e como pagam as despesas da casa.
> 3. Proponho categorias para as despesas e ajustamos juntos.
> 4. Pesquiso os movimentos que não reconheço e pergunto-te só os que ficarem por esclarecer.
> 5. Comparo com o vosso orçamento, se tiverem um (se não, proponho um).
> 6. Mostro quanto cada um contribui para a família e sugiro onde dá para poupar.
> 7. No fim, entrego um dashboard que podem consultar e atualizar todos os meses.
>
> **Do que preciso:** os extratos dos últimos 12 meses de todas as contas que pagam despesas da família (conta conjunta, contas pessoais e cartões de crédito). Excel ou CSV são melhores do que PDF.
>
> **Quanto tempo demora:** a primeira vez é a mais demorada, porque há mais perguntas. Nos meses seguintes é rápido, porque guardo as vossas respostas.
>
> **Privacidade:** os extratos ficam só nesta conversa e não os envio para outros serviços. Uso a pesquisa na web apenas para nomes de empresas. O dashboard é privado até decidirem partilhá-lo.
>
> Isto não é aconselhamento financeiro: são as vossas contas, organizadas.

**Durante o trabalho:**
- **No início de cada passo**, diz numa frase o que vais fazer e porquê. Por exemplo: "Agora vou ver se os saldos batem certo, para garantir que não falta nenhum extrato."
- **Quando encontrares um problema**, explica-o com um exemplo concreto do extrato e diz o que precisas.
- **Quando fizeres perguntas**, dá opções sempre que possível e aceita "não sei".

**No fim**, explica como ler o dashboard:
- **"Ver":** muda entre tudo, só a família e os gastos pessoais de cada pessoa.
- **Médias:** são por mês, e cada conta é dividida pelos meses que o seu extrato cobre.
- **Meses com asterisco:** estão incompletos (nem todas as contas têm extrato desse mês inteiro).
- **Contribuições:** o que cada pessoa põe na família (transferências para a conta conjunta e despesas da família pagas da conta pessoal).
- **Divisão justa:** compara o que cada um contribui com uma divisão a meias e com uma proporcional ao rendimento.
- **Extraordinários:** ficam fora das médias para não as distorcer, mas aparecem numa secção própria.
- **Olho:** esconde os valores e desfoca as descrições, para tirar screenshots.

Depois explica como atualizar nos meses seguintes e oferece o lembrete mensal (passo 9).

## O que a skill traz

`SKILL_DIR` é a pasta onde está este ficheiro. Os scripts precisam de Python 3.9+ com `pip install pandas openpyxl xlrd pdfplumber` (instala o que faltar; em alguns ambientes é preciso `--break-system-packages`).

| Ficheiro | Para que serve |
|---|---|
| `scripts/ler_extratos.py` | Lê CSV, XLSX, XLS e PDF, deteta as colunas e junta tudo em `movimentos.csv`. Remove repetidos de extratos sobrepostos. `--inspecionar FICHEIRO` mostra o que percebeu. |
| `scripts/verificar.py` | Confirma períodos, continuidade de saldos, buracos entre extratos e meses vazios. Escreve `verificacao.md`. |
| `scripts/classificar.py` | Aplica as regras, deteta transferências internas, contribuições e pagamentos de cartão. Escreve `movimentos_classificados.csv` e `por_identificar.csv`. |
| `scripts/analisar.py` | Médias, subscrições, duplicados, aumentos, comissões, despesas anuais, extraordinários, contribuições e divisão justa. Escreve `analise.json`. |
| `scripts/construir_dashboard.py` | Gera `Orcamento_Familiar.html` a partir de `assets/dashboard.html`. |
| `scripts/enable_banking.py` | Opcional: descarrega movimentos diretamente dos bancos. Ver `references/enable_banking.md`. |
| `assets/regras_base.csv` | Regras para centenas de comerciantes e serviços portugueses. É copiado para a pasta de trabalho como `regras.csv`. |
| `references/` | `config.md` (formato do config), `categorias.md`, `identificacao.md`, `otimizacao.md`, `divisao_justa.md`, `agendamento.md`, `enable_banking.md`. Lê cada um quando chegares ao passo correspondente. |

Todos os scripts recebem `--config CAMINHO/config.json` e trabalham na pasta desse config. Corre-os sempre sem esconder erros e confirma o código de saída. Um script que falhou em silêncio leva a um dashboard com dados antigos.

## Pasta de trabalho

Tudo o que a família precisa para atualizar no mês seguinte fica numa pasta `orcamento-familiar/`. De preferência fica junto dos extratos, na pasta do utilizador; pergunta onde guardar se não for óbvio. Conteúdo:
- `config.json`: pessoas, contas, orçamento, sugestões e decisões gerais.
- `regras.csv`: regras de classificação (as da família no topo, as base por baixo).
- `decisoes.md`: registo das respostas do utilizador, com data (o "porquê" das regras).
- Gerados pelos scripts: `movimentos.csv`, `movimentos_meta.json`, `verificacao.md`, `movimentos_classificados.csv`, `por_identificar.csv`, `analise.json`, `Orcamento_Familiar.html`.
- `estado.json`: escrito pelo `construir_dashboard.py`. Guarda a data da última atualização e até que dia vai o extrato de cada conta. É o que a atualização mensal e o lembrete agendado consultam para saber o que é novo.
- No config, `dashboard_url`: o link do dashboard publicado, para as atualizações irem sempre para o mesmo link.

Se a pasta já tiver `config.json`, estás numa **atualização**: salta para "Atualização mensal".

## Passo 1. Extratos

1. Pede os extratos. O utilizador pode indicar a pasta onde estão (se tiveres acesso ao computador dele) ou anexá-los à conversa. O ideal são **12 meses** de **todas as contas que pagam coisas da família**: conta conjunta, contas pessoais e cartões de crédito. CSV ou Excel são mais fiáveis do que PDF; se o banco permitir exportar, sugere esse formato.
2. Lista os ficheiros e corre `ler_extratos.py --inspecionar` em cada um. Diz ao utilizador o que encontraste, por ficheiro: banco provável, período e número de movimentos.
3. Se um ficheiro não for lido corretamente:
   - indica as colunas à mão com `"mapa"` no config (ver `references/config.md`);
   - se for um PDF que falha, abre as páginas como imagem para perceber o formato e escreve um parser em `orcamento-familiar/parsers/<banco>.py` com a função `ler(caminho)`.
   Não avances com ficheiros mal lidos.

## Passo 2. Contas, pessoas e como se paga o orçamento

Faz estas perguntas (de escolha múltipla, com resposta livre, quando a interface o permitir). Junta as que puderes numa só ronda e adapta ao que já sabes pelos ficheiros:

1. **Quem faz parte do orçamento:** as pessoas que contribuem com dinheiro. Os filhos só entram como categoria de despesa.
2. **De quem é cada conta e cada ficheiro:** conjunta, pessoal de alguém, ou cartão de crédito de alguém (e qual a conta que o paga).
3. **Como entra o dinheiro para as despesas da família:**
   - Se há conta conjunta: transferências mensais fixas (de quanto?), depósitos em numerário, outras entradas.
   - Se não há: quem paga o quê, se fazem acertos (MB WAY, transferências), que despesas são sempre da família.
   - Se só existe uma conta conjunta: tudo é da família. Pergunta só de onde vem o dinheiro.
4. **Despesas da família pagas da conta pessoal:** renda, luz, supermercado, creche… Quais e por quem.
5. **Ajudas de fora:** pais, avós ou outros que transferem dinheiro, e para que conta.
6. **Nomes nas transferências:** como aparece o nome de cada pessoa e de quem ajuda (por exemplo "TRF. DE ANA P COSTA"). Ajuda a detetar contribuições.
7. **Contas que não estão nos extratos:** Revolut, poupança, corretoras. São poupança ou contas de gastos?
8. **O que não aparece nos extratos:** cartões refeição, cheque-creche, numerário regular, despesas pagas por outros.
9. Opcional: **rendimento líquido mensal de cada pessoa**, para a divisão proporcional. Se não quiserem dizer, a skill usa os salários que aparecerem nos extratos.

Escreve o `config.json` (formato e exemplo em `references/config.md`). Regista as respostas em `decisoes.md`. Depois:
- Corre `ler_extratos.py --config` e a seguir `verificar.py --config`.
- **Período de cada conta:** se o `verificar` sugerir `inicio`/`fim` lidos do cabeçalho do extrato, põe-nos no config.
- **Quebras de saldo, buracos entre extratos ou meses vazios:** quase sempre falta um extrato ou houve linhas mal lidas. Mostra o problema ao utilizador e pede o que falta.
- **Ficheiros sem saldo** (comum nos cartões): pede o saldo inicial e final do extrato e confirma as contas.
- **Sinal dos valores no cartão:** se o `ler_extratos` avisar que as compras aparecem positivas, usa `"sinal": "invertido"` nessa conta.

## Passo 3. Categorização

1. Corre `classificar.py` (na primeira vez cria `regras.csv` a partir das regras base). Lê `references/categorias.md`.
2. Mostra a proposta numa tabela curta: categoria, média mensal, peso e 2 ou 3 exemplos de movimentos.
3. Mostra também o que foi detetado automaticamente, para o utilizador confirmar:
   - contribuições por pessoa;
   - transferências internas;
   - pagamentos de cartão;
   - poupança e investimento;
   - "Conta própria fora da análise".
4. Pergunta o que ajustar:
   - nomes de categorias;
   - juntar ou separar categorias;
   - categorias próprias da família (animais, igreja, desporto dos filhos…);
   - **o que é da família e o que é pessoal**.
   Sem conta conjunta, usa `"ambito_por_categoria"` no config para dizer que categorias pagas das contas pessoais são sempre da família.
5. Aplica as respostas em `regras.csv`. As regras da família vão **acima** das regras base (a primeira regra que encaixa ganha). Para renomear uma categoria, muda-a em todas as regras. Volta a correr `classificar.py`.

## Passo 4. Movimentos por identificar

1. Abre `por_identificar.csv` (vem ordenado do maior para o menor valor).
2. **Pesquisa primeiro**, seguindo `references/identificacao.md`: prefixos dos bancos, processadores de pagamento, Racius e códigos CAE. Só classifica com evidência sólida. Se a pesquisa sugerir algo mas não tiveres a certeza, guarda a pista para a pergunta.
3. **Depois pergunta ao utilizador**, em lotes de até 8, começando pelos maiores. Para cada movimento indica:
   - data, conta e valor;
   - o que encontraste na pesquisa;
   - os movimentos do mesmo dia (coluna `mesmo_dia`);
   - quantas vezes se repete (coluna `parecidos`).
   Movimentos pequenos e únicos (menos de 10 €) podem ir juntos para "Pequenas despesas", com autorização do utilizador.
4. Aproveita as rondas para confirmar o que `analisar.py` assinala:
   - **Extraordinários:** movimentos grandes e únicos. Ficam como tipo X, fora das médias mas visíveis.
   - **Despesas anuais:** IRS, seguros, IUC. Ficam na média, com sugestão de reserva mensal.
   - **MB WAY e levantamentos grandes.**
   - **Transferências para pessoas fora da família.**
   - **Contas próprias fora da análise.**
5. Regista cada resposta:
   - **Comerciante que se repete:** regra por padrão em `regras.csv`.
   - **Movimento único:** regra com `id_movimento`.
   - **Em todos os casos:** uma linha em `decisoes.md`.
   Se o utilizador explicar um movimento, guarda a explicação em `notas_movimentos` no config ou na coluna `nota` da regra; aparece no dashboard.
6. Repete até "Por identificar" ficar abaixo de cerca de 2 % da despesa, ou até o utilizador dizer que chega.

## Passo 5. Orçamento planeado

Pergunta se têm um orçamento mensal (ficheiro, Excel, foto ou escrito na conversa).
- **Se sim:**
  1. Lê-o.
  2. Mapeia cada linha para categorias e, se for preciso, subcategorias. Mostra o mapeamento e confirma.
  3. Preenche `"orcamento"` no config.
  4. Se uma linha inclui algo que não passa pelos extratos (cartão refeição, por exemplo), usa `extra_mensal` com o valor indicado pelo utilizador e explica na `nota`.
- **Se não:**
  1. Propõe um orçamento a partir das médias da família, arredondado.
  2. Inclui as reservas para despesas anuais.
  3. Marca `"orcamento_proposto": true` e pede ajustes.

## Passo 6. Contribuições e divisão justa

Lê `references/divisao_justa.md` e corre `analisar.py`.
1. **Explica as contribuições:**
   - quanto cada pessoa (e cada ajuda de fora) põe na família por mês;
   - quanto vai para a conta conjunta e quanto paga diretamente;
   - em que meses (só os meses em que todas as contas têm extrato completo).
2. **Pergunta que divisão preferem:** a meias, proporcional ao rendimento ou outra regra deles. Mostra as diferenças sem julgar. É um tema delicado: usa um tom neutro e factual.
3. **Guarda no config:** `"divisao": {"metodo": ...}` e, se tiverem indicado, `"rendimentos"`.
4. **Se algo não bater certo** (por exemplo, uma pessoa parece contribuir muito mais), revê com o utilizador o que está a contar como contribuição antes de tirar conclusões. Pode haver despesas pagas diretamente que ainda não estão marcadas como da família, ou reembolsos.

## Passo 7. Sugestões de otimização

Lê `references/otimizacao.md` e usa `analise.json`:
- subscrições e duplicados;
- aumentos de preço;
- comissões bancárias;
- numerário;
- despesas anuais;
- tendências;
- desvios ao orçamento.

Escreve 3 a 7 sugestões em `"sugestoes"` no config: `{"titulo", "texto", "poupanca_mensal"}`.
- Cada sugestão cita os valores dos extratos.
- Só preenche `poupanca_mensal` quando o valor sai diretamente dos movimentos (por exemplo, o custo de uma subscrição duplicada).
- Nada de produtos financeiros nem promessas de poupança.

## Passo 8. Dashboard

1. Corre `construir_dashboard.py --config`.
2. **Verifica antes de entregar.**
   - Se tiveres um browser sem interface (Playwright ou Chromium), abre o HTML, confirma que não há erros na consola e lê de volta a despesa média e as contribuições.
   - Compara esses valores com `analise.json`.
   - Experimenta o botão do olho: não pode sobrar nenhum valor em euros visível.
3. **Entrega.**
   - Se tiveres a ferramenta de artifacts, publica-o como artifact privado e guarda o link em `"dashboard_url"` no config. Nas atualizações, publica no mesmo link (passa esse link à ferramenta) para a família não ficar com vários dashboards. Se não tiveres a ferramenta, envia o ficheiro.
   - Explica o filtro "Ver" (Tudo, Família, cada pessoa).
   - Explica o botão do olho: esconde os valores e desfoca as descrições, para screenshots.
4. **Resume em poucas linhas:**
   - despesa média mensal da família;
   - as três maiores categorias;
   - contribuição de cada pessoa;
   - as duas sugestões com mais impacto;
   - o que ficou por identificar.

## Passo 9. Lembrete mensal (agendamento)

No fim da primeira análise, pergunta se a família quer um lembrete mensal para atualizar o dashboard. O lembrete é uma tarefa agendada no Claude. Por exemplo, no dia 5 de cada mês, que é quando os extratos do mês anterior já estão disponíveis. A tarefa:
1. vê se já há extratos novos na pasta;
2. se houver, faz a atualização e conta o que mudou;
3. se não houver, pergunta se já os têm e explica onde os pôr.

Como criar:
- **Ferramentas:** usa as ferramentas de tarefas agendadas que esta sessão tiver (procura-as se não estiverem carregadas). Não uses agendamentos que só existem dentro da sessão atual: desaparecem quando a conversa fecha.
- **Instrução completa:** cada execução começa uma conversa nova, sem memória desta. A instrução da tarefa tem de ser completa e independente. Usa o modelo em `references/agendamento.md`, com os caminhos verdadeiros da pasta de trabalho e dos extratos.
- **Computador:** se a pasta estiver no computador do utilizador, a tarefa precisa do computador ligado e da app do Claude aberta à hora marcada. Explica isto ao utilizador.
- **Confirmação:** confirma com o utilizador o dia, a hora e se as execuções avançam sozinhas ou pedem aprovação. Diz o que ficou definido.
- **Sem ferramentas:** se esta sessão não tiver ferramentas de agendamento, diz que não consegues criar o lembrete daqui. Sugere pedir o lembrete ao Claude numa conversa que o permita, ou pôr um lembrete no calendário com a frase "atualizar o Orçamento Familiar com os extratos de <mês>".

## Atualização mensal

0. **Lê o estado:** abre `config.json`, `estado.json` e `decisoes.md` para saber até onde ia cada conta e o que já foi decidido. Diz ao utilizador de que meses precisas.
1. **Junta os extratos novos** na pasta dos extratos, ou descarrega-os com `enable_banking.py descarregar`. Se os padrões em `ficheiros` não os apanharem, acrescenta-os ao config.
   - Para a mesma conta, não juntes API e extratos manuais do mesmo período: as descrições diferem e os movimentos ficariam a dobrar.
   - Usa `desde` e `ate` nas fontes para separar os períodos.
2. **Atualiza os períodos:** se o config tiver `fim` nas contas, atualiza-o para o fim dos extratos novos. Com `"janela_meses": 12` no config, o dashboard mostra sempre os últimos 12 meses e as médias refletem o último ano. Os movimentos antigos continuam nos ficheiros. Propõe esta opção na primeira atualização.
3. **Corre os scripts:**
   - `ler_extratos.py`, `verificar.py` e `classificar.py`;
   - pergunta só pelos movimentos novos em "Por identificar";
   - `analisar.py` e `construir_dashboard.py`;
   - publica no link guardado em `dashboard_url`.
4. **Conta o que mudou:**
   - o mês novo face à média;
   - categorias que subiram;
   - subscrições novas;
   - autorizações do Enable Banking a expirar (se usarem).

Para automatizar (descarregar todos os dias e rever as dúvidas uma vez por semana ou por mês), segue `references/enable_banking.md`.

## Formato das regras (`regras.csv`)

Colunas: `id_movimento, conta, padrao, sinal, valor_min, valor_max, data_de, data_ate, tipo, categoria, subcategoria, ambito, contribuinte, nota`.
- `conta`: vazio para todas; o id de uma conta; ou `tipo:conjunta`, `tipo:pessoal`, `tipo:cartao`. Várias separadas por `|`.
- `padrao`: expressão regular, sem distinção de maiúsculas.
- `sinal`: `saida`, `entrada` ou vazio.
- `tipo`:
  - `D` despesa;
  - `R` rendimento;
  - `T` transferência interna;
  - `C` pagamento de cartão;
  - `P` poupança e investimento;
  - `X` extraordinário.
- `ambito`: `familia` ou o id de uma pessoa. Vazio usa o da conta: conjunta é família; pessoal é do titular.
- `contribuinte`: id de quem contribui (para entradas na conta conjunta que não foram detetadas automaticamente).
- Linhas começadas por `#` são comentários.

Exemplos:
```
,ana,SENHORIO,saida,,,,,D,Casa & contas,Renda,familia,,Renda paga pela Ana da conta dela
,,NIA ROSA,,,,,,D,Saúde,Consultas & exames,,,Clínica de fisioterapia (resposta da família)
3f2a9c1b7d4e,,,,,,,,X,Extraordinários,Compra do carro,familia,,Entrada do carro novo
,conjunta,DEP[ÓO]SITO,entrada,500,,,,T,Contribuição,rui,familia,rui,Depósitos em numerário do Rui na conjunta
```

## Erros que já aconteceram e não podem repetir-se

- **Pagamentos do cartão de crédito contados como despesa** além das compras do cartão (dobro). Se o extrato do cartão não estiver incluído, o pagamento é a única informação: o classificador marca-o como "Cartão de crédito sem extrato" e deves pedir o extrato.
- **Transferências da conta pessoal para a conjunta contadas como despesa.**
- **Dividir por 12 uma conta com menos meses de extrato.**
- **Linhas perdidas em PDFs** (por exemplo, a primeira linha de cada página). As quebras de saldo denunciam-nas; confirma vendo a página como imagem.
- **Sinal trocado no cartão**, ou datas sem ano.
- **Reembolsos tratados como rendimento.** Reembolsos de seguros de saúde e devoluções de lojas descontam na categoria onde aconteceram.
- **Assumir que uma transferência para alguém é despesa**, ou que uma empresa desconhecida é de certo tipo, sem pesquisar e perguntar.
- **Esconder a saída dos scripts** (`> /dev/null`): uma falha silenciosa produz um dashboard com dados antigos.
- **Esquecer despesas da família pagas da conta pessoal.** A contribuição dessa pessoa parece menor do que é e a despesa da família também.
