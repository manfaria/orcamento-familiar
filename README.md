# Orçamento Familiar · skill para o Claude

Transforma os extratos bancários da família num dashboard de orçamento familiar. Tudo numa conversa com o Claude: ele lê os extratos, pergunta como a família organiza as contas, categoriza as despesas, identifica os movimentos estranhos contigo, compara com o orçamento planeado, calcula quanto cada um contribui e sugere onde poupar.

Pensada para famílias em Portugal: lê extratos de bancos portugueses (CSV, Excel ou PDF) e conhece centenas de comerciantes e serviços portugueses. Identifica empresas desconhecidas pelo Racius e pelo código CAE. Tudo em português europeu.

![Dashboard Orçamento Familiar com dados fictícios](docs/dashboard.png)

*Exemplo com uma família e dados inventados.*

## O que o dashboard mostra
- **Despesa média mensal:** da família e de cada pessoa. Cada conta é dividida pelos meses que o seu extrato cobre.
- **Categorias e subcategorias:** quem paga cada uma e os maiores movimentos.
- **Evolução mês a mês:** gráfico e tabela, com os meses incompletos assinalados.
- **Orçamento planeado vs real**, ou uma proposta de orçamento a partir das médias.
- **Contribuições para a família:** o que cada pessoa transfere para a conta conjunta e o que paga diretamente.
- **Divisão justa:** a meias ou proporcional ao rendimento.
- **Sugestões de otimização com valores dos extratos:**
  - subscrições duplicadas;
  - aumentos de preço;
  - comissões;
  - despesas anuais para reservar.
- **Fora das despesas:** rendimentos, poupança, extraordinários, custos fixos e o que não aparece nos extratos (cartão refeição, cheque-creche).
- **Pesquisa de todos os movimentos.**
- **Botão com um olho:** esconde todos os valores e desfoca as descrições, para partilhar screenshots.

## Como funciona
1. **Extratos:** indicas a pasta dos extratos ou anexa-los à conversa.
2. **Contas:** o Claude pergunta quem tem que contas, se há conta conjunta, de onde vem o dinheiro do orçamento e o que fica fora dos extratos.
3. **Categorias:** propõe uma categorização e ajusta-a contigo.
4. **Movimentos desconhecidos:** pesquisa-os e depois pergunta-te, em pequenos lotes.
5. **Orçamento:** pergunta se tens um orçamento mensal para comparar.
6. **Contribuições:** calcula as contribuições e a divisão justa.
7. **Sugestões:** sugere otimizações com base no que viu.
8. **Dashboard:** gera o dashboard.
9. **Lembrete mensal:** se quiseres, cria uma tarefa agendada no Claude que, todos os meses, verifica se já há extratos novos e atualiza o dashboard (ou pergunta-te por eles).

No mês seguinte, basta juntar os extratos novos: as regras e as decisões ficam guardadas e só aparecem perguntas sobre movimentos novos. O dashboard é atualizado no mesmo link e pode mostrar sempre os últimos 12 meses. Quem quiser pode automatizar a recolha dos movimentos com a [Enable Banking](https://enablebanking.com/) (ver `references/enable_banking.md`).

## Instalar
- **Claude (claude.ai e app de computador):** comprime a pasta `orcamento-familiar` num ficheiro zip e carrega-o como skill personalizada nas definições do Claude. É preciso ter a execução de código ativa.
- **Claude Code:** copia a pasta para `~/.claude/skills/orcamento-familiar/`.

Requisitos: Python 3.9 ou superior, com `pandas`, `openpyxl`, `xlrd` e `pdfplumber`. O Claude instala o que faltar. Para a ligação automática aos bancos: `pyjwt`, `cryptography` e `requests`.

## Começar
Escreve ao Claude algo como:
> Quero fazer o orçamento familiar a partir dos nossos extratos. Estão na pasta Extratos.

ou anexa os extratos e pede:
> Usa a skill Orçamento Familiar com estes extratos.

## Privacidade
- Os extratos são tratados na tua sessão com o Claude. A skill não envia dados para outros serviços. A pesquisa na web só é usada para nomes de empresas.
- O dashboard é um único ficheiro HTML, privado até decidires partilhá-lo.
- Antes de partilhar um screenshot, carrega no olho para esconder os valores e os nomes.
- Na ligação automática aos bancos, a chave privada fica só no teu computador e o acesso é apenas de leitura.

Esta skill não é aconselhamento financeiro.

## Estrutura
```
orcamento-familiar/
├── SKILL.md                    instruções para o Claude
├── scripts/
│   ├── comum.py                funções partilhadas
│   ├── ler_extratos.py         lê CSV, Excel e PDF; deteta colunas; remove repetidos
│   ├── verificar.py            períodos, continuidade de saldos, extratos em falta
│   ├── classificar.py          regras, transferências internas, contribuições, cartões
│   ├── analisar.py             médias, subscrições, duplicados, contribuições, divisão
│   ├── construir_dashboard.py  gera Orcamento_Familiar.html
│   └── enable_banking.py       opcional: movimentos diretamente dos bancos
├── assets/
│   ├── dashboard.html          modelo do dashboard
│   └── regras_base.csv         regras para comerciantes portugueses
├── references/                 config, categorias, identificação, otimização,
│                               divisão justa, agendamento, Enable Banking
└── docs/dashboard.png          imagem de exemplo (dados fictícios)
```

## Contribuir
Sugestões bem-vindas, sobretudo:
- **Regras para comerciantes** que faltem em `assets/regras_base.csv`.
- **Formatos de extrato** de bancos portugueses que o leitor não perceba à primeira. Envia um exemplo com dados inventados, nunca um extrato real.

## Autor e licença
Criado por Manuel Faria. Licença MIT (ver `LICENSE`).
