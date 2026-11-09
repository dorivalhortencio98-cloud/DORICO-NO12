# FUTEBOL200 PRO — Motor modular (versão técnica 0.2)

## Estado real
- Implementado: conexão Football-Data.org, ingestão de jogos encerrados, recortes casa/fora, estimativas Poisson para 1X2, dupla chance, ambas marcam e totais de gols, comparação com odds fornecidas e abstenção quando faltam dados.
- Estrutura preparada, mas **não implementada**: integração de escanteios, cartões, finalizações, desfalques, escalações, arbitragem e jogos ao vivo. `extensions.py` define campos para futuras fontes autorizadas.
- **Não está pronto para comercialização**: falta validação estatística, checagem de licenças de dados/uso comercial, fontes de odds, proteção de credenciais em servidor, controle de usuários e limites de acesso.
- As probabilidades são estimativas não calibradas, não garantias. O modelo ignora dependência entre gols, força dos adversários, contexto, lesões e outros fatores.

## Requisitos
Python 3.10+; somente biblioteca padrão. Internet e token válido para a API.

## Testes sem API
No diretório do projeto:
`python -m unittest discover -s tests -v`

## Como executar no PowerShell (não compartilhe a chave)
```powershell
$env:FOOTBALL_DATA_TOKEN = Read-Host "Cole sua chave Football-Data.org"
python main.py --competition BSA --home-id 64 --away-id 65
```
Os IDs 64 e 65 são **somente exemplos**; descubra os IDs reais com a API. Sem odds, o programa devolve `NO_RECOMMENDATION` por segurança.

Para analisar odds verificadas, crie seu próprio JSON no formato de `examples/odds.example.json` e use `--odds-file caminho.json`. Os valores do arquivo de exemplo são **fictícios** e não devem orientar apostas reais.

## Decisão do motor
- Exige no mínimo 5 jogos encerrados do mandante em casa e 5 do visitante fora (últimos 10 de cada).
- Usa média entre ataque e defesa dos dois times para parâmetros Poisson.
- Calcula vários mercados, mas devolve no máximo um candidato se probabilidade >=55%, vantagem sobre probabilidade implícita >=4 pontos percentuais e valor esperado positivo.
- Sem odds ou amostra suficiente, devolve `NO_RECOMMENDATION`.
- `MODEL_CANDIDATE` significa candidato matemático **não validado**, e não recomendação final.

## Próximas implementações
1. Catálogo confiável de IDs e nomes de equipes; temporadas e paginação.
2. Normalização por força de adversários, tempo e competição; backtesting e calibração.
3. Fontes legais para odds, lesões, escalações, cartões, escanteios e ao vivo, com horários de atualização.
4. Checagem de autorização de uso comercial e limites por provedor.
5. Backend com licenças individuais, 20 consultas/dia por cliente, segurança e logs.
6. Painel visual **por último**.

Nunca inclua tokens em arquivos, screenshots ou mensagens.

## Atualização 0.3 — módulos extras
Adicionado `futebol200/advanced.py` e `advanced_cli.py` com **ingestão padronizada de
estatísticas externas** de escanteios, cartões amarelos, finalizações e chutes no alvo.
Calcula probabilidades exploratórias por Poisson apenas com >=8 partidas válidas
por mercado. Aceita odds verificadas em JSON e identifica no máximo um candidato
matemático, nunca uma recomendação validada. Não inventa dados faltantes.

Desfalques e escalações são **recebidos e preservados como contexto**, mas ainda
**não alteram as probabilidades**: não existe modelo de impacto de atletas validado.
O modo ao vivo recebe minuto/eventos, verifica atualização (máx. 10 minutos) e
**não calcula recomendações ao vivo**, pois ainda falta modelo temporal validado.
Nenhuma API de lesões, escalações, escanteios, cartões ou live foi integrada: o
arquivo JSON deve vir de uma fonte com permissão de uso. Não use exemplos como
estatísticas reais. Os mercados extras são protótipos estatísticos, sem backtest.

Teste: `python -m unittest discover -s tests -v`
Uso: `python advanced_cli.py --stats-file examples/extra.example.json`

## Atualização 0.4 — seguir com os dados disponíveis
Foram adicionados `consultar_times.py` e `diagnostico.py` para facilitar a execução
sem interface gráfica. Não há integração Sportmonks confirmada: a tela do plano
gratuito mostra 4 ligas e 180 chamadas, mas não esclarece periodicidade, campos
estatísticos disponíveis nem autorização de redistribuição comercial.

No PowerShell, na pasta do projeto:
```powershell
$env:FOOTBALL_DATA_TOKEN = Read-Host 'Cole sua chave Football-Data.org'
python consultar_times.py --competition BSA
python diagnostico.py --competition BSA --home-id ID_MANDANTE --away-id ID_VISITANTE
```
Substitua `ID_MANDANTE` e `ID_VISITANTE` pelos números da listagem. O diagnóstico
mostra probabilidades exploratórias de gols **sem sugerir apostas**. O motor
`main.py` segue exigindo odds verificadas para avaliar vantagem. Os outros
mercados só funcionam com dados externos autorizados e suficientes; não há
cobertura automática de escanteios, cartões, finalizações, desfalques,
escalações ou eventos ao vivo neste pacote.
