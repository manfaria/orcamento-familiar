# Contexto num projeto do assistente

Depois da primeira análise, a família vai querer voltar: perguntar quanto gastou em restaurantes, classificar uma despesa nova, acrescentar uma linha ao orçamento. Cada conversa nova começa sem memória. Para não repetir tudo, o contexto fica guardado num projeto do assistente (no Claude, um projeto; noutras plataformas, o espaço equivalente com ficheiros e instruções partilhados por todas as conversas, se existir).

O mecanismo tem três partes:
1. **Um documento de contexto no projeto**, gerado pelo `contexto_projeto.py`.
2. **Instruções do projeto** que mandam ler esse documento e mantê-lo atualizado.
3. **A regra de atualizar o documento** depois de cada alteração.

## 1. Gerar e guardar o documento
1. Corre `contexto_projeto.py --config <pasta>/config.json` depois de `construir_dashboard.py`.
2. O script escreve `contexto_projeto.md`, com:
   - onde está cada coisa: dashboard, pasta de trabalho, extratos;
   - pessoas e contas, com o período de cada uma e os meses usados nas médias;
   - como se calculam os números;
   - médias por categoria e subcategoria, da família e de cada pessoa;
   - orçamento planeado vs real, contribuições e evolução mensal;
   - as categorias em uso;
   - as decisões da família (copiadas de `decisoes.md`);
   - como fazer uma alteração;
   - o que está em aberto.
3. **Guarda-o no projeto** com o nome `contexto-orcamento-familiar.md`.
   - Se tiveres uma ferramenta para escrever documentos no projeto, usa-a e substitui sempre o mesmo documento (nunca cries cópias com nomes diferentes).
   - Se não tiveres, envia o ficheiro e pede à família para o carregar nos ficheiros do projeto, apagando a versão anterior.
4. **O que não está nos ficheiros não entra no documento.** Uma decisão importante tomada em conversa vai primeiro para `decisoes.md`, com data. Só depois se gera o documento. Assim o documento nunca diz uma coisa e os ficheiros outra.

## 2. Instruções do projeto
- O script escreve `instrucoes_projeto.txt` com o texto já preenchido: caminho da pasta de trabalho e link do dashboard. Se os scripts correrem noutro sítio que não o computador da família (por exemplo, numa cópia da pasta), põe em `"pasta_familia"` no config o caminho como a família o vê, para o documento e as instruções o mostrarem.
- Normalmente não consegues alterar as instruções do projeto. Dá o texto à família numa caixa de código, pronto a colar, e diz onde: nas instruções do projeto, nas definições do projeto.
- Ajusta o texto ao que a família te disse: língua, se quer que perguntes sempre antes de classificar, se há mais pessoas a usar o projeto.
- **Porque é preciso:** a skill só entra em ação quando a conversa é claramente sobre o orçamento. As instruções do projeto aplicam-se a todas as conversas do projeto, mesmo a uma pergunta curta.

## 3. Manter o contexto atualizado
Volta a correr o script e substitui o documento no projeto, na mesma conversa, sempre que:
- houver extratos novos (atualização mensal ou tarefa agendada);
- mudar uma regra, uma categoria ou um âmbito;
- a família responder a dúvidas (por identificar, adiantamentos, despesas pagas por outros);
- mudar o orçamento planeado, a divisão justa ou o que fica fora dos extratos.

No fim, diz numa linha o que mudou no documento.

Se a conversa não conseguir acabar uma alteração (por exemplo, por falta de acesso à pasta), escreve em `decisoes.md` o que ficou por fazer. A conversa seguinte encontra-o no documento.

## Acesso à pasta de trabalho
- **O documento serve para responder; a pasta serve para alterar.** O documento chega para perguntas sobre os números. Para mudar alguma coisa, a conversa precisa da pasta de trabalho: no computador da família (no Claude, com a conversa ligada ao computador) ou num zip anexado.
- **Sem acesso à pasta, não alteres nada.** Diz o que farias e pede o acesso. Uma alteração feita só no dashboard perde-se na atualização seguinte.

## Privacidade
- **O documento tem valores e categorias de gastos de cada pessoa.** Antes de o guardar, confirma quem tem acesso ao projeto.
- **A opção `pessoal` do config também se aplica ao documento:**
  - `"total"`: o documento mostra só o total pessoal de cada pessoa;
  - `"categorias"`: mostra as categorias, sem descrições de movimentos (o documento nunca as tem).
- **Nunca guardes no projeto** os extratos, números de conta, IBAN, nem as chaves da Enable Banking.
