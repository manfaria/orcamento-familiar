# Ligação automática aos bancos (Enable Banking)

Opcional, para quem quer deixar de descarregar extratos à mão. A Enable Banking é um agregador europeu (PSD2) com acesso de leitura às contas: movimentos e saldos, sem poder fazer pagamentos.

## Antes de começar
- **Bancos suportados:** confirma que os bancos da família aparecem (`enable_banking.py bancos --pais PT`, ou a lista em "Link accounts" no Control Panel). Alguns emissores de cartões de crédito não estão disponíveis (a Wizink, por exemplo). Para essas contas, continua com os extratos manuais: a skill junta as duas fontes sem problema.
- **Cada titular autoriza a sua conta:** a autenticação forte é feita na app do banco de cada pessoa. Ninguém deve ligar a conta de outra pessoa sem o acordo dela.
- **Autorização temporária:** dura até 180 dias. Depois é preciso voltar a ligar (o script avisa 15 dias antes).
- **Limite de atualizações:** pelas regras europeias, um acesso automático pode atualizar no máximo cerca de 4 vezes por dia por conta. Uma vez por dia chega.

## Configurar (uma vez)
1. Criar conta no Control Panel da Enable Banking e uma aplicação em **Production**:
   - o browser descarrega um ficheiro `.pem` com a chave privada;
   - fica-se com um **Application ID**;
   - regista-se um redirect URL (por exemplo `https://localhost/retorno`; não precisa de existir, só serve para copiar o código do endereço).
2. Para uso pessoal, usar **"Link accounts"** na aplicação para ligar as próprias contas. A aplicação fica "Restricted" mas "Active" e só vê as contas ligadas.
3. No computador da família, com `pip install pyjwt cryptography requests`, define as variáveis de ambiente:
   ```
   EB_APP_ID=<application id>
   EB_KEY=/caminho/seguro/<application id>.pem
   EB_REDIRECT=https://localhost/retorno
   ```
4. Para cada banco:
   1. Corre `python enable_banking.py ligar --banco "<nome exato>" --pasta orcamento-familiar/eb`.
   2. Autoriza no banco e cola o endereço de retorno.
   3. Põe cada `uid` mostrado na conta certa do config: `"enable_banking": {"uid": "..."}`.
5. No config, acrescenta a fonte da API a cada conta, sem sobrepor períodos com os extratos manuais:
   ```json
   "ficheiros": [{"padrao": "Extratos/santander_*.csv", "ate": "2026-09-30"},
                 {"padrao": "eb/eb_rui.csv", "desde": "2026-10-01"}]
   ```

## Usar
- `python enable_banking.py descarregar --pasta orcamento-familiar/eb --config orcamento-familiar/config.json --desde 2026-10-01` escreve `eb_<conta>.csv` no formato que `ler_extratos.py` lê.
- `python enable_banking.py estado --pasta orcamento-familiar/eb` mostra quanto falta para cada autorização expirar.

## Automatizar (descarregar sozinho e rever as dúvidas com o assistente)
A combinação mais simples, que mantém a chave só no computador da família:
1. **Agendador do sistema** (Agendador de Tarefas no Windows, launchd ou cron no Mac/Linux): corre `enable_banking.py descarregar` todos os dias.
2. **Tarefa agendada no assistente** (semanal ou mensal), se ele tiver acesso à pasta no computador (no Claude, as tarefas agendadas):
   1. corre `ler_extratos.py`, `verificar.py`, `classificar.py`, `analisar.py` e `construir_dashboard.py`;
   2. atualiza o dashboard;
   3. envia as dúvidas novas (movimentos por identificar, autorizações a expirar).

Cada execução da tarefa agendada começa sem memória da conversa anterior. Por isso, as decisões têm de estar escritas em `regras.csv`, `config.json` e `decisoes.md`. Escreve o pedido da tarefa como uma instrução completa: onde está a pasta, que scripts correr e o que reportar.

## Segurança
- A chave `.pem` nunca vai para o dashboard, para a conversa nem para repositórios. Guarda-a fora da pasta partilhada, se a pasta estiver sincronizada na nuvem.
- O dashboard só recebe movimentos já classificados.
- Para revogar: apagar a aplicação no Control Panel ou retirar o acesso na app do banco.
