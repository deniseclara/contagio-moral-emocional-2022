# -*- coding: utf-8 -*-
"""
Funções compartilhadas pelas etapas do pipeline.

Reúne o que precisa valer igual para as publicações dos candidatos e para as
respostas recebidas. Se a limpeza ou o dicionário mudarem, mudam para os dois
lados ao mesmo tempo, que é a condição para comparar a carga do emissor com a
carga da resposta (seção 3.6.3 da dissertação).
"""
import os, re, html, unicodedata
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRUTOS = os.path.join(RAIZ, "dados", "brutos")
DERIVADOS = os.path.join(RAIZ, "dados", "derivados")
SAIDAS = os.path.join(RAIZ, "saidas")
# Classificação já feita, distribuída com o repositório. As etapas 5 e 7 leem
# daqui quando as etapas 2 a 4 não foram executadas na máquina.
CLASSIFICADOS = os.path.join(RAIZ, "dados", "classificados")
MFD = os.path.join(RAIZ, "dicionarios", "mfd_ptbr_alpha.dic")
for p in (DERIVADOS, SAIDAS):
    os.makedirs(p, exist_ok=True)

JANELA_INI, JANELA_FIM = "2022-08-16", "2022-10-30"
CANDIDATOS = {"lula": "Lula", "bolsonaro": "Bolsonaro", "ciro": "Ciro Gomes"}

# As onze categorias do MFD-BR. Cada fundamento aparece em virtude e em vício,
# e a seção 3.4.2 conta as duas juntas: o que a medida registra é a presença do
# repertório, não a polaridade do juízo.
CATEGORIAS = {1: "cuidado_virtude", 2: "cuidado_vicio",
              3: "justica_virtude", 4: "justica_vicio",
              5: "lealdade_virtude", 6: "lealdade_vicio",
              7: "autoridade_virtude", 8: "autoridade_vicio",
              9: "santidade_virtude", 10: "santidade_vicio",
              11: "moralidade_geral"}
INDIVIDUALIZANTES = [1, 2, 3, 4]              # cuidado e justiça
# No capitulo a tendencia chama-se COESIVA (Zacarias, Almeida e Modesto, 2024).
# O nome da constante e das colunas n_vin e b_vin fica como esta, porque as
# colunas ja estao publicadas nos CSV classificados.
VINCULANTES = [5, 6, 7, 8, 9, 10]             # lealdade, autoridade, santidade
GERAL = [11]

# Lista curta e explícita. Uma lista longa de stopwords removeria termos que o
# próprio MFD-BR classifica, e o dicionário é aplicado depois desta limpeza.
STOPWORDS = set("""a o e é de do da em um uma os as no na para com por que se
não mais como mas ao dos das num numa pelo pela até isso ela entre depois sem
mesmo aos seus quem nas me esse eles você essa num nem suas meu às minha numa
pelos elas qual nós lhe deles essas esses pelas este dele tu te vocês vos lhes
meus minhas teu tua teus tuas nosso nossa nossos nossas dela delas esta estes
estas aquele aquela aqueles aquelas isto aquilo eu ele nos lá aqui ali já
também só sua seu foi ser tem são está estão ter há ou quando muito
""".split())

_URL = re.compile(r"https?://\S+|www\.\S+")
_MENCAO = re.compile(r"@\w+")
_HASH = re.compile(r"#(\w+)")
_NUM = re.compile(r"\d+")
_ESPACO = re.compile(r"\s+")
_NAO_LETRA = re.compile(r"[^a-zà-ÿ\s]")


def normalizar_para_neural(texto):
    """Texto para o classificador de valência.

    O modelo foi treinado sobre publicações de rede social, então o texto é
    mantido próximo do original. Só menções e endereços viram marcadores, para
    que o nome de um perfil não pese na classificação.
    """
    t = html.unescape(str(texto or ""))
    t = _URL.sub("url", t)
    t = _MENCAO.sub("@usuario", t)
    return _ESPACO.sub(" ", t).strip()


def limpar_para_dicionario(texto):
    """Texto para o dicionário moral, devolvido como lista de tokens.

    Aqui o tratamento é o convencional de análise lexical, porque o dicionário
    compara palavra a palavra e não interpreta contexto: minúsculas, remoção de
    endereços, menções, números e pontuação, e corte das stopwords.
    """
    t = html.unescape(str(texto or "")).lower()
    t = _URL.sub(" ", t)
    t = _MENCAO.sub(" ", t)
    t = _HASH.sub(r"\1", t)          # a hashtag vira a palavra que ela carrega
    t = _NUM.sub(" ", t)
    t = unicodedata.normalize("NFC", t)
    t = _NAO_LETRA.sub(" ", t)
    return [p for p in _ESPACO.sub(" ", t).strip().split() if p and p not in STOPWORDS]


def limpar_para_topicos(texto):
    """Texto para o agrupamento temático.

    Limpeza leve, de propósito. A representação numérica é produzida por um
    modelo de linguagem, que lê a frase inteira e se apoia na ordem e nas
    palavras funcionais para captar sentido. Cortar stopwords e pontuação antes
    de gerar a representação degrada o agrupamento. O corte de stopwords ocorre
    depois, na extração das palavras que distinguem cada grupo.
    """
    t = html.unescape(str(texto or "")).lower()
    t = _URL.sub(" ", t)
    t = _MENCAO.sub(" ", t)
    t = _NUM.sub(" ", t)
    return _ESPACO.sub(" ", t).strip()


def carregar_mfd(caminho=MFD):
    """Lê o .dic no formato LIWC e devolve (termos exatos, prefixos).

    O formato traz o mapa de categorias entre duas linhas de '%' e, depois, uma
    entrada por linha com a palavra seguida dos números de categoria. O asterisco
    ao fim da palavra indica prefixo, e vale para qualquer flexão.

    O arquivo do repositório MFD-BR começa com marca de ordem de byte, por isso
    utf-8-sig.
    """
    exatos, prefixos = defaultdict(set), []
    with open(caminho, encoding="utf-8-sig") as f:
        linhas = [l.rstrip("\n") for l in f]
    marcas = [i for i, l in enumerate(linhas) if l.strip() == "%"]
    corpo = linhas[marcas[1] + 1:] if len(marcas) >= 2 else linhas
    for l in corpo:
        if not l.strip():
            continue
        partes = l.split()
        termo, cats = partes[0], {int(c) for c in partes[1:] if c.isdigit()}
        if not cats:
            continue
        if termo.endswith("*"):
            prefixos.append((termo[:-1], cats))
        else:
            exatos[termo] |= cats
    prefixos.sort(key=lambda x: -len(x[0]))     # prefixo mais longo tem prioridade
    return dict(exatos), prefixos


def categorias_do_token(tok, exatos, prefixos):
    if tok in exatos:
        return exatos[tok]
    for p, cats in prefixos:
        if tok.startswith(p):
            return cats
    return set()


def medir_moral(texto, exatos, prefixos):
    """Devolve a contagem por categoria e os três indicadores de presença.

    A seção 3.4.2 mede PRESENÇA: cada indicador vale 1 quando o texto traz ao
    menos um termo da categoria correspondente, e 0 quando não traz nenhum.
    """
    toks = limpar_para_dicionario(texto)
    cont = defaultdict(int)
    for t in toks:
        for c in categorias_do_token(t, exatos, prefixos):
            cont[c] += 1
    n_ind = sum(cont[c] for c in INDIVIDUALIZANTES)
    n_vin = sum(cont[c] for c in VINCULANTES)
    n_ger = sum(cont[c] for c in GERAL)
    return {
        "n_tokens": len(toks),
        "n_moral": n_ind + n_vin + n_ger,
        "n_ind": n_ind, "n_vin": n_vin, "n_ger": n_ger,
        "b_ind": int(n_ind > 0), "b_vin": int(n_vin > 0), "b_ger": int(n_ger > 0),
        **{f"mfd_{CATEGORIAS[c]}": cont[c] for c in CATEGORIAS},
    }


def classificar_valencia(textos, cache_csv, lote=64):
    """Aplica o classificador de valência, com cache em disco.

    O modelo é o `pysentimiento` de análise de sentimento em português, cuja
    base é o BERTweet.BR (CARNEIRO et al., 2025), treinado sobre cem milhões de
    tweets brasileiros. Devolve, para cada texto, as probabilidades de positivo,
    negativo e neutro, que somam um.

    O cache é gravado a cada lote. Numa máquina sem placa de vídeo a passagem
    completa leva horas, e uma interrupção no meio não deve custar o trabalho já
    feito. A chave do cache é o identificador, então cada corpus precisa do seu
    próprio arquivo de cache.
    """
    import csv, time
    import pandas as pd

    feito = {}
    if os.path.exists(cache_csv):
        c = pd.read_csv(cache_csv, dtype={"id": str}).drop_duplicates("id", keep="last")
        feito = {r.id: (r.p_pos, r.p_neg, r.p_neu) for r in c.itertuples()}
        print(f"   cache: {len(feito):,} já classificados")

    pendentes = [(i, t) for i, t in textos if i not in feito]
    print(f"   a classificar: {len(pendentes):,}", flush=True)
    if not pendentes:
        return feito

    # o torch em CPU se atrapalha com excesso de linhas de execução
    import torch
    torch.set_num_threads(max(1, (os.cpu_count() or 4) // 2))
    from pysentimiento import create_analyzer
    an = create_analyzer(task="sentiment", lang="pt")

    # gravação por acréscimo. Reescrever o arquivo inteiro a cada lote torna o
    # custo quadrático, e com 48 mil respostas isso domina o tempo de execução.
    novo = not os.path.exists(cache_csv)
    t0 = time.time()
    with open(cache_csv, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if novo:
            w.writerow(["id", "p_pos", "p_neg", "p_neu"])
        for k in range(0, len(pendentes), lote):
            bloco = pendentes[k:k + lote]
            saida = an.predict([normalizar_para_neural(t) for _, t in bloco])
            for (i, _), s in zip(bloco, saida):
                p = s.probas
                feito[i] = (p.get("POS", 0.0), p.get("NEG", 0.0), p.get("NEU", 0.0))
                w.writerow([i, *(f"{v:.6f}" for v in feito[i])])
            f.flush()
            n = min(k + lote, len(pendentes))
            if k % (lote * 10) == 0 or n == len(pendentes):
                dt = time.time() - t0
                falta = (len(pendentes) - n) / max(n / dt, 1e-9)
                print(f"   {n:,}/{len(pendentes):,}  "
                      f"{n / dt:.1f} por segundo  faltam {falta / 60:.0f} min", flush=True)
    return feito
