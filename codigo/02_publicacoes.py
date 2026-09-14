# -*- coding: utf-8 -*-
"""
ETAPA 2 — Classificação das publicações (seções 3.4.1 e 3.4.2).

Dimensão emocional (3.4.1). O classificador devolve, para cada publicação, as
probabilidades de positivo, negativo e neutro, que somam um. Delas saem duas
variáveis:

    intensidade = 1 − P(neutro)                 quanta emoção há no texto
    assimetria  = P(negativo) − P(positivo)     qual valência predomina

Dimensão moral (3.4.2). O MFD-BR é aplicado por contagem direta e a medida é de
PRESENÇA: cada indicador vale 1 quando o texto traz ao menos um termo da
categoria, e 0 quando não traz nenhum.

    b_ind   cuidado ou justiça
    b_vin   lealdade, autoridade ou santidade
    b_ger   moralidade genérica

As contagens brutas também são gravadas, porque a seção 3.4.3 descreve o
repertório de cada campanha fundamento a fundamento.

Saída: dados/derivados/publicacoes_classificadas.csv
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from comum import (DERIVADOS, CATEGORIAS, carregar_mfd, medir_moral,
                   classificar_valencia)

CACHE = os.path.join(DERIVADOS, "_cache_valencia_publicacoes.csv")


def main():
    df = pd.read_csv(os.path.join(DERIVADOS, "corpus.csv"), dtype={"id": str})
    df = df[~df.sem_texto].copy()
    print(f"[3.4] {len(df):,} publicações com texto\n")

    print("[3.4.1] valência, com o classificador em português brasileiro")
    probs = classificar_valencia(list(zip(df.id, df.texto)), CACHE)
    df["p_pos"] = df.id.map(lambda i: probs[i][0])
    df["p_neg"] = df.id.map(lambda i: probs[i][1])
    df["p_neu"] = df.id.map(lambda i: probs[i][2])
    df["intensidade"] = 1 - df.p_neu
    df["assimetria"] = df.p_neg - df.p_pos
    print(f"   intensidade  M = {df.intensidade.mean():.3f}  "
          f"DP = {df.intensidade.std():.3f}  "
          f"mín. = {df.intensidade.min():.3f}  máx. = {df.intensidade.max():.3f}")
    print(f"   assimetria   M = {df.assimetria.mean():.3f}  "
          f"DP = {df.assimetria.std():.3f}  "
          f"mín. = {df.assimetria.min():.3f}  máx. = {df.assimetria.max():.3f}")
    print("   declarado na 3.4.1: intensidade 0,446 (0,314), de 0,024 a 0,995")
    print("                       assimetria −0,074 (0,487), de −0,989 a 0,988\n")

    print("[3.4.2] carga moral, pelo MFD-BR")
    exatos, prefixos = carregar_mfd()
    print(f"   dicionário: {len(exatos)} termos exatos e {len(prefixos)} prefixos")
    med = pd.DataFrame([medir_moral(t, exatos, prefixos) for t in df.texto],
                       index=df.index)
    df = pd.concat([df, med], axis=1)
    for r, c in [("individualizantes", "b_ind"), ("vinculantes", "b_vin"),
                 ("moralidade geral", "b_ger")]:
        print(f"   usa {r:<18} {100 * df[c].mean():5.1f}%")
    algum = ((df.b_ind + df.b_vin + df.b_ger) > 0)
    q = df.b_ind + df.b_vin + df.b_ger
    print(f"   {100 * algum.mean():.1f}% acionam algum indicador  "
          f"({100 * (q == 1).mean():.1f}% um, {100 * (q == 2).mean():.1f}% dois, "
          f"{100 * (q == 3).mean():.1f}% três)")
    print("   declarado na 3.4.2: 15,2% / 25,3% / 12,8% | 41,2% | 30,3 / 9,6 / 1,3\n")

    df.to_csv(os.path.join(DERIVADOS, "publicacoes_classificadas.csv"),
              index=False, encoding="utf-8")
    print(f"gravado: publicacoes_classificadas.csv  ({len(df):,} linhas)")
    print("\nocorrências por categoria do dicionário:")
    print(df[[f"mfd_{n}" for n in CATEGORIAS.values()]].sum().to_string())


if __name__ == "__main__":
    main()
