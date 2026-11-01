# Identificar movimentos desconhecidos

Objetivo: classificar com evidência, nunca por palpite. Pesquisa primeiro e só depois pergunta, já com pistas.

## 1. Ler a descrição
Os bancos portugueses juntam prefixos e códigos ao nome do comerciante:
- `COMPRA 1234 …`: compra com cartão (1234 são os últimos dígitos do cartão), seguida do nome e da localidade do comerciante.
- `DD …` / `DEB DIR` / `Débito direto`: débito direto (luz, água, telecomunicações, seguros, ginásio, creche).
- `PAG SERV` / `Pagamento de serviços` / `Pag. Estado`: pagamento por referência multibanco (entidade + referência).
- `TRF` / `TRF. P/O` / `TRF MB WAY P/` / `Transferência emitida`: transferências; o nome a seguir é o destinatário.
- `LEV` / `Levantamento`: numerário.
- Códigos como `-E01234`, `IMED` ou números longos: transferências imediatas ou referências internas.

## 2. Processadores de pagamento
Estes nomes **não** são o comerciante. Escondem quem recebeu: Hipay, Adyen, Stripe, PayPal, SumUp, Easypay, Ifthenpay, Eupago, Mollie, Klarna, Viva Wallet, Checkout.com, Worldline, Revolut Business, Paysafe.
- Às vezes o comerciante vem a seguir (`PAYPAL *AIRBNB`, `SUMUP *ZE MANEL`).
- Se não vier, procura pistas no próprio extrato: o mesmo valor todos os meses (subscrição), movimentos no mesmo dia noutras contas, ou a cidade.
- Depois pergunta ao utilizador. Exemplos: o mesmo valor via Hipay em meses seguidos pode ser um anúncio num site de classificados; dois pagamentos via Hipay no mesmo dia, de contas diferentes, podem ser um alojamento de férias pago a meias.

## 3. Pesquisar empresas na web
Usa a pesquisa na web só com o nome da empresa (nunca com nomes de pessoas nem outros dados da família):
- **Racius** (racius.com) e **eInforma** (einforma.pt): atividade, código CAE, morada e NIF.
- Pesquisa geral pelo nome e localidade (Google Maps e páginas da empresa).

Usa o código CAE para chegar à categoria:

| CAE | Atividade | Categoria |
|---|---|---|
| 47110 / 47111 | Supermercados e hipermercados | Supermercado & alimentação |
| 47220 / 47230 / 47240 | Talho, peixaria, padaria | Supermercado & alimentação (Mercado & talho) |
| 56101 / 56102 / 56103 / 56104 / 56105 / 56106 / 56107 | Restaurantes | Restauração |
| 56301 / 56302 / 56303 / 56304 | Cafés, bares e pastelarias | Restauração (Cafés & pastelarias) |
| 47300 | Combustíveis | Transportes |
| 45200 | Reparação automóvel | Transportes (Manutenção do carro) |
| 47730 / 47740 | Farmácias e artigos médicos | Saúde |
| 86210 / 86220 / 86230 / 86901 / 86906 | Médicos, dentistas, clínicas, fisioterapia | Saúde |
| 85100 / 85201 / 85310 / 88910 | Creche, ensino básico e secundário | Educação & filhos |
| 85510 / 85520 / 85593 | Desporto, artes e explicações | Educação & filhos ou Desporto (perguntar para quem) |
| 93110 / 93130 / 93192 | Instalações desportivas, ginásios | Desporto |
| 96021 / 96022 | Cabeleireiros e estética | Vestuário & cuidado pessoal |
| 47710 / 47721 / 47722 | Vestuário e calçado | Vestuário & cuidado pessoal |
| 47591 / 47592 / 47540 | Móveis, decoração, eletrodomésticos | Compras & casa |
| 55111 / 55201 / 55204 | Hotéis e alojamento local | Lazer & viagens |
| 79110 / 79120 | Agências de viagens | Lazer & viagens |
| 75000 | Veterinários | Animais de estimação |
| 43210 / 43221 / 43320 / 43390 | Eletricistas, canalizadores, obras | Casa & contas (Manutenção & reparações) |
| 81100 / 68322 | Condomínios e gestão de imóveis | Casa & contas (Condomínio) |
| 18120 / 74200 | Gráficas e fotografia | Presentes & donativos ou Compras & casa (perguntar) |

Uma empresa pode ter vários CAE. Se a atividade principal não esclarecer, pergunta.

## 4. Perguntar
- Lotes de até 8 movimentos, do maior para o menor.
- Para cada um: data, conta, valor, descrição, o que a pesquisa encontrou e os movimentos do mesmo dia.
- Oferece opções quando houver uma hipótese forte ("Parece uma clínica de fisioterapia (CAE 86906). Foi isso?").
- Aceita "não sei". O movimento fica "Por identificar" com uma nota, e voltas a ele mais tarde ou na atualização seguinte.
- Pergunta também se é da família ou pessoal, quando não for óbvio.

## 5. Registar
- **Comerciante que se repete:** regra por padrão em `regras.csv`, acima das regras base.
- **Movimento único:** regra com `id_movimento` (está em `por_identificar.csv`).
- **Sempre:** uma linha em `decisoes.md` com a data, a pergunta e a resposta.
- **Explicações que valem a pena ver no dashboard:** coluna `nota` da regra.
