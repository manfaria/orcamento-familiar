# Formato das regras (`regras.csv`)

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

As regras da família ficam **acima** das regras base: a primeira regra que encaixa ganha. Para renomear uma categoria, muda-a em todas as regras.
