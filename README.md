# Contágio moral-emocional e engajamento no Twitter: dados

Dados e código descritivo da dissertação *Contágio moral-emocional e engajamento no Twitter: emoção, moralidade e difusão na eleição presidencial brasileira de 2022*, de Denise Clara Santos Santana, orientada pelo Prof. Dr. Pedro Santos Mundim, no Programa de Pós-Graduação em Ciência Política e Relações Internacionais da Universidade Federal de Goiás.

**Esta é uma publicação parcial.** O repositório traz o corpus, a classificação de emoção, moral e tema de cada publicação e de cada resposta, e o código que reconstrói a parte descritiva do capítulo de métodos. O código dos modelos de regressão e os resultados das hipóteses serão acrescentados depois da defesa.

## A pergunta

O conteúdo emocional dos tweets dos candidatos de 2022 está associado a maior engajamento, e esse efeito se intensifica quando a emoção se articula à linguagem moral?

## Como rodar

```bash
pip install -r requirements.txt
```

O caminho curto usa a classificação que acompanha o repositório e leva poucos segundos.

```bash
python codigo/01_corpus.py && python codigo/05_descritivas.py && python codigo/07_conferir.py
```

O caminho completo refaz a classificação a partir do texto.

```bash
python codigo/01_corpus.py && python codigo/02_publicacoes.py && python codigo/03_topicos.py && python codigo/04_respostas.py && python codigo/05_descritivas.py && python codigo/07_conferir.py
```

Em máquina sem placa de vídeo, a etapa 2 leva perto de meia hora e a etapa 4 leva algumas horas. As duas gravam cache em disco e retomam de onde pararam.

As etapas 5 e 7 leem a classificação gerada na máquina, em `dados/derivados/`, quando ela existe, e a distribuída, em `dados/classificados/`, quando não existe.

## As etapas

| arquivo | o que faz | seção da dissertação |
|---|---|---|
| `codigo/comum.py` | limpeza de texto, dicionário moral e classificador, compartilhados | 3.2.1, 3.4 |
| `codigo/01_corpus.py` | aplica os filtros e constitui o corpus | 3.2 |
| `codigo/02_publicacoes.py` | mede emoção e moral nas publicações | 3.4.1, 3.4.2 |
| `codigo/03_topicos.py` | agrupa as publicações por vocabulário | 3.4.4 |
| `codigo/04_respostas.py` | mede emoção e moral nas respostas | 3.6.3 |
| `codigo/05_descritivas.py` | gera as tabelas e quadros descritivos | 3.2 a 3.5 |
| `codigo/07_conferir.py` | compara cada número descritivo com o que o texto declara | 3.2 a 3.6 |

A numeração pula a etapa 6, reservada aos modelos.

## Os dados

### Brutos

`dados/brutos/ited_chaves.csv` traz identificador, candidato, data de partição e identificador do tweet referenciado, para 5.352 publicações. Extraído do **Interfaces Twitter Elections Dataset**, o ITED-Br (IASULAITIS et al., 2025), que é a fonte dos identificadores.

Dois campos dessa tabela decidem quem entra no corpus, e nenhum dos dois está no conteúdo recuperado. A janela de campanha é aplicada sobre a **data de partição do ITED-Br**, e não sobre o carimbo de tempo da publicação. Pelo carimbo, a janela devolveria 3.506 publicações em lugar de 3.546. E é o **identificador do tweet referenciado** que separa publicação original de continuação de sequência.

`dados/brutos/candidatos/{lula,bolsonaro,ciro}.csv` trazem o conteúdo recuperado das três contas, com texto e métricas de engajamento. São 5.352 linhas somadas, das quais 71 registram tentativa que falhou.

`dados/brutos/respostas/respostas_coletadas.csv` traz as respostas recebidas, com as colunas `resposta_id`, `tweet_pai`, `candidato`, `texto`, `data` e `erro`. São 268.699 linhas de tentativa de recuperação, das quais 48.124 são respostas válidas em 2.407 publicações. `respostas_ids.csv` repete só os identificadores.

`dados/brutos/topicos_referencia.csv` guarda uma partição temática alternativa, de treze grupos (ver Reprodutibilidade).

`dicionarios/mfd_ptbr_alpha.dic` é o Moral Foundations Dictionary em português brasileiro (CARVALHO et al., 2020), com setecentos termos em onze categorias.

### Classificados

`dados/classificados/publicacoes_classificadas.csv` tem uma linha por publicação do corpus, N = 2.716. Traz o conteúdo e o engajamento, as probabilidades de valência, a intensidade e a assimetria emocional, a contagem de termos de cada uma das onze categorias do dicionário, os três indicadores binários de carga moral e o grupo temático.

`dados/classificados/respostas_classificadas.csv` tem uma linha por resposta, N = 48.124, em 2.407 publicações. Traz o texto e as mesmas medidas.

| coluna | o que mede |
|---|---|
| `p_pos`, `p_neg`, `p_neu` | probabilidades do classificador de valência |
| `intensidade` | `p_pos + p_neg`, de 0 a 1 |
| `assimetria` | `p_neg − p_pos`, de −1 a 1. Positivo indica predomínio negativo |
| `n_tokens` | tokens depois da limpeza |
| `mfd_*` | termos do dicionário em cada uma das onze categorias |
| `n_ind`, `n_vin`, `n_ger` | termos individualizantes (cuidado e justiça), vinculantes (lealdade, autoridade e santidade) e de moralidade geral |
| `b_ind`, `b_vin`, `b_ger` | presença de ao menos um termo de cada eixo, 0 ou 1 |
| `topico`, `topico_rotulo` | grupo temático e seus cinco termos mais distintivos, só nas publicações |
| `tem_moral` | presença de qualquer termo moral, só nas respostas |

### Do bruto ao corpus

| etapa | publicações |
|---|---|
| identificadores na janela de 16/08 a 30/10/2022 | 3.546 |
| conteúdo recuperado | 3.515 |
| publicações originais, excluídas as continuações | 2.717 |
| com texto, unidade efetiva da análise | 2.716 |

Uma publicação de Ciro Gomes foi recuperada só com mídia, sem texto. Entra na contagem do corpus e sai da classificação.

### Os usuários não aparecem na base

A coleta não gravou nome nem perfil de quem respondeu. No texto das respostas, toda menção a conta foi substituída por `@usuario`. A substituição não altera a classificação, porque a limpeza de texto do pipeline já troca menções por esse mesmo marcador antes do classificador e as remove antes do dicionário. Conferido nas 48.127 respostas com texto, sem nenhuma diferença.

## Duas decisões de medida

**A carga moral é presença, e não proporção.** Três indicadores binários disjuntos, um por eixo. A operacionalização segue a de Dantas (2023) sobre o mesmo dicionário.

**Vício e virtude contam juntos.** Uma publicação aborda um fundamento quando contém qualquer termo dele, seja do polo da virtude, seja do polo do vício. A medida indica se o fundamento aparece no texto, e não se ele é elogiado ou condenado.

## Reprodutibilidade

O agrupamento temático tem uma parte aleatória. Para que ele dê o mesmo resultado a cada execução, o código fixa o valor inicial dessa parte aleatória, chamado de semente. Mesmo assim, os resultados podem mudar de um computador para outro em dois pontos.

O primeiro é o **agrupamento temático, que muda com a versão das bibliotecas instaladas**. Antes de formar os grupos, o BERTopic reduz o número de dimensões com que cada texto é representado. Essa redução dá resultados diferentes em versões diferentes da biblioteca, mesmo com a semente fixa. Uma execução de julho de 2026 encontrou treze grupos. Outra, de agosto, no mesmo computador e com a mesma semente, encontrou dez. A dissertação usa os **dez grupos**, que são os de `dados/classificados/`. Os treze estão em `dados/brutos/topicos_referencia.csv`, para comparação.

O segundo é o **classificador de valência**. Para um mesmo texto, ele devolve sempre o mesmo resultado. Versões diferentes do modelo, porém, podem devolver probabilidades um pouco diferentes. Por isso a etapa 7 aceita uma pequena margem e mostra o valor obtido ao lado do valor declarado na dissertação.

## Instrumentos

O classificador de valência é o de análise de sentimento em português da biblioteca `pysentimiento` (PÉREZ et al., 2021), cuja base é o **BERTweet.BR** (CARNEIRO et al., 2025), treinado sobre cem milhões de tweets brasileiros pelo MeLLL da Universidade Federal Fluminense.

O agrupamento temático usa **BERTopic** (GROOTENDORST, 2022).

Nenhum dos dois foi validado contra codificação humana neste corpus. A validade é herdada dos trabalhos que construíram cada instrumento, e a limitação está declarada na seção 3.7 da dissertação.

## Licenças

O **código**, em `codigo/`, está sob licença MIT. Ver `LICENCA-CODIGO.md`.

Os **dados**, em `dados/`, estão sob **CC BY-NC-SA 4.0**. Ver `LICENCA-DADOS.md`.

Os dados seguem a licença do ITED-Br, a CC BY-NC-SA 4.0. Ela proíbe o uso comercial, exige a citação do artigo do ITED-Br e obriga qualquer trabalho derivado a usar a mesma licença.

## Referências dos dados e instrumentos

CARNEIRO, Fernando; VIANNA, Daniela; CARVALHO, Jonnathan; PLASTINO, Alexandre; PAES, Aline. BERTweet.BR: a pre-trained language model for tweets in Portuguese. *Neural Computing and Applications*, v. 37, n. 6, p. 4363-4385, 2025.

CARVALHO, Flavio; OKUNO, Helder Yukio; BARONI, Lais; GUEDES, Gustavo. A Brazilian Portuguese Moral Foundations Dictionary for fake news classification. In: INTERNATIONAL CONFERENCE OF THE CHILEAN COMPUTER SCIENCE SOCIETY, 39., 2020, Coquimbo. *Proceedings* [...]. 2020.

DANTAS, Leonardo Feitosa. *Electoral discourse of right-wing candidates in redistributionist districts*: a study of changing moral foundations. 2023. Dissertação (Mestrado) – Escola Brasileira de Administração Pública e de Empresas, Fundação Getulio Vargas, Rio de Janeiro, 2023.

GROOTENDORST, Maarten. BERTopic: neural topic modeling with a class-based TF-IDF procedure. *arXiv*, 2022.

IASULAITIS, Sylvia; VALEJO, Alan D. B.; GRECO, Bruno C.; PERILLO, Vinícius G.; MESSIAS, Guilherme H.; VICARI, Igor. The Interfaces Twitter Elections Dataset: construction process and characteristics of big social data during the 2022 presidential elections in Brazil. *PLOS ONE*, v. 20, n. 2, e0316626, 2025. DOI: 10.1371/journal.pone.0316626.

PÉREZ, Juan Manuel et al. pysentimiento: a Python toolkit for sentiment analysis and social NLP tasks. *arXiv*, 2021.
