# Lembrete mensal com uma tarefa agendada

O objetivo é que a família não se esqueça de atualizar o dashboard. Uma vez por mês, o Claude verifica se já há extratos novos. Se houver, atualiza o dashboard e conta o que mudou. Se não houver, pergunta se já os têm e explica onde os pôr.

## Antes de criar
Confirma com o utilizador:
- **Quando:** sugere o dia 5 de cada mês de manhã, quando os extratos do mês anterior já estão disponíveis. Evita horas certas (por exemplo, 8:50 em vez de 9:00).
- **Onde estão as coisas:** o caminho da pasta de trabalho (`config.json`) e da pasta dos extratos. Se estiverem no computador do utilizador, a tarefa precisa do computador ligado e da app do Claude aberta à hora marcada.
- **Aprovações:** se as execuções podem avançar sozinhas ou se devem pedir aprovação. Uma tarefa que pede aprovação fica parada se ninguém estiver a ver; diz isso ao utilizador.
- **Avisos:** como quer ser avisado (notificação, email), se a ferramenta o permitir.

Usa as ferramentas de tarefas agendadas da sessão (procura-as se não estiverem carregadas). Não uses agendamentos que só existem dentro da conversa atual. Depois de criar, diz ao utilizador o dia, a hora, a forma de aprovação que ficou e como pode alterar ou apagar a tarefa.

## Modelo da instrução da tarefa
Cada execução começa uma conversa nova, sem memória. Copia este modelo e substitui o que está entre `< >`:

```
Orçamento Familiar: verificação mensal de extratos novos.

Usa a skill orcamento-familiar. A pasta de trabalho é <caminho da pasta de trabalho> (tem config.json,
regras.csv, decisoes.md e estado.json). Os extratos estão em <caminho da pasta dos extratos>.
O dashboard está publicado em <dashboard_url>; atualiza sempre esse mesmo link.

1. Lê estado.json para saber até que dia vai cada conta e quando foi a última atualização.
2. Procura na pasta dos extratos ficheiros novos ou com movimentos posteriores a essas datas.
   Se a família usar a Enable Banking, corre primeiro: enable_banking.py descarregar (ver config.json).
3. Se NÃO houver extratos novos de todas as contas:
   envia uma mensagem curta a perguntar se já têm os extratos de <mês anterior>, diz de que contas
   faltam e lembra como os exportar e onde os pôr. Não alteres nada e termina.
4. Se houver: faz a "Atualização mensal" da skill (ler_extratos, verificar, classificar, analisar,
   construir_dashboard) e publica o dashboard no mesmo link.
5. Envia um resumo: despesa do mês novo face à média, categorias que subiram, subscrições novas,
   avisos (extratos em falta, autorizações da Enable Banking a expirar) e, em lotes de até 8,
   os movimentos novos que ficaram por identificar, com data, conta, valor e contexto.
   As respostas da família são registadas em regras.csv e decisoes.md na próxima conversa.

Nunca inventes valores: tudo vem dos extratos. Não envies os extratos para outros serviços.
```

## Sem ferramentas de agendamento
Se a sessão não tiver ferramentas de tarefas agendadas, diz que não consegues criar o lembrete daqui. Sugere:
- pedir o lembrete ao Claude numa conversa que permita tarefas agendadas, usando o modelo acima;
- ou pôr um lembrete no calendário: "atualizar o Orçamento Familiar com os extratos de <mês>". Nesse dia basta abrir uma conversa e pedir "atualiza o Orçamento Familiar".
