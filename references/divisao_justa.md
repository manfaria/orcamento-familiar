# Contribuições e divisão justa

## Contribuições
Calculadas só nos meses em que **todas** as contas têm extrato completo (`janela_comum`), para comparar o mesmo período.

Para cada pessoa, por mês:
- **Para a conjunta:** transferências da pessoa para a conta conjunta (detetadas por par entre contas, pelo nome em `nomes_banco` ou por regra com `contribuinte`), menos o que a conjunta lhe transferiu de volta (reembolsos e levantamentos).
- **Pago diretamente:** despesas com âmbito `familia` pagas de uma conta pessoal ou cartão de que a pessoa é a única titular.
- **Total** = para a conjunta + pago diretamente.

Contribuidores externos (pais, avós): entradas deles na conta conjunta.

**Despesa da família:** todas as despesas com âmbito `familia`, de qualquer conta. "Sobra / falta" = total das contribuições − despesa da família. Uma sobra constante quer dizer que a conjunta acumula dinheiro; uma falta constante quer dizer que está a gastar a reserva ou que há contribuições que não foram detetadas.

### Antes de concluir que alguém contribui mais
Confirma com a família:
- se há despesas da família pagas da conta pessoal que ainda estão como pessoais;
- se há depósitos em numerário na conjunta (sem nome) que são de alguém;
- se há transferências entre as contas pessoais do casal para acertos;
- se a conjunta devolveu dinheiro a alguém por despesas que essa pessoa adiantou.

É comum uma pessoa parecer contribuir muito mais só porque faltava marcar despesas da família pagas da conta pessoal da outra, ou um depósito em numerário que passou por outra conta antes de chegar à conjunta.

## Métodos de divisão
Primeiro desconta a ajuda externa: `a dividir = despesa da família − contribuições externas`.

| Método | Quanto cabe a cada um | Quando faz sentido |
|---|---|---|
| Igual | a dividir ÷ número de pessoas | Rendimentos parecidos, ou se preferem simplicidade |
| Proporcional ao rendimento | a dividir × rendimento da pessoa ÷ soma dos rendimentos | Rendimentos diferentes: cada um contribui com a mesma percentagem do que ganha |
| Proporcional com mínimo pessoal | Cada pessoa guarda primeiro um valor igual para si; o resto divide-se na proporção do rendimento que sobra | Quando um rendimento é baixo e a proporção simples deixaria essa pessoa sem margem |
| Personalizado | Percentagens decididas pela família | Acordos próprios (por exemplo, quem tem mais tempo em casa contribui menos em dinheiro) |

O dashboard mostra as duas primeiras. Para as outras, calcula-as e explica-as na conversa ou numa sugestão.

**Rendimentos:** usa os indicados pela família (`rendimentos` no config). Se não houver, usa a média dos salários que aparecem nos extratos e diz de onde veio o valor. Se faltar o rendimento de alguém, não mostres a proporcional.

## Tom
Dinheiro entre casais é um tema delicado. Apresenta números, não juízos. Não digas quem "deve" mais. Mostra a diferença face a cada método e pergunta qual a família prefere.
