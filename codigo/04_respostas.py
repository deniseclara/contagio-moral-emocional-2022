# -*- coding: utf-8 -*-
"""
ETAPA 4 — Classificação das respostas recebidas (seção 3.6.3, H5).

Aplica às respostas o mesmo instrumento usado nas publicações. É essa igualdade
de régua que torna H5 testável: comparar a carga do emissor com a carga da
resposta só faz sentido se as duas foram medidas do mesmo jeito.

UMA ADAPTAÇÃO NECESSÁRIA
As respostas têm mediana de seis palavras depois da limpeza, e 46% ficam com
cinco ou menos. Nesse regime os três eixos separados produziriam categorias raras
demais, então a medida moral da resposta é um indicador único, a resposta contém
ou não vocabulário moral. A variável da publicação passa a ser a proporção de
suas respostas que contêm.

DADOS DE ENTRADA
Lê `dados/brutos/respostas/respostas_coletadas.csv`, com o texto. No arquivo
distribuído, toda menção a conta aparece como `@usuario`. A limpeza já substitui
menções por esse marcador, então a classificação é idêntica à feita sobre o
texto original.

Saída: dados/derivados/respostas_classificadas.csv
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from comum import (BRUTOS, DERIVADOS, carregar_mfd, medir_moral,
                   classificar_valencia)

ENTRADA = os.path.join(BRUTOS, "respostas", "respostas_coletadas.csv")
IDS = os.path.join(BRUTOS, "respostas", "respostas_ids.csv")
CACHE = os.path.join(DERIVADOS, "_cache_valencia_respostas.csv")
SAIDA = os.path.join(DERIVADOS, "respostas_classificadas.csv")


def main():
    if not os.path.exists(ENTRADA):
        print("O arquivo com o texto das respostas não está presente.\n")
        print(f"O repositório traz apenas os identificadores, em\n   {IDS}\n")
        print("Para refazer esta etapa é preciso recuperar o conteúdo de cada\n"
              "identificador na plataforma e gravar um arquivo com as colunas\n"
              "resposta_id, tweet_pai, candidato, texto, data e erro.")
        sys.exit(1)

    rp = pd.read_csv(ENTRADA, dtype={"resposta_id": str, "tweet_pai": str},
                     encoding="utf-8", on_bad_lines="skip")
    print(f"[bruto] {len(rp):,} linhas de tentativa de recuperação")

    val = rp[rp.erro.isna() | (rp.erro.astype(str).str.strip() == "")].copy()
    print(f"[válidas] {len(val):,}")

    # o incidente de 28/07/2026, em que um segundo processo gravou no mesmo
    # arquivo, deixou três identificadores repetidos e uma linha rasgada
    bem = val.resposta_id.fillna("").str.isdigit() & val.tweet_pai.fillna("").str.isdigit()
    n_ruins = int((~bem).sum())
    val = val[bem]
    n_dup = int(val.resposta_id.duplicated().sum())
    val = val.drop_duplicates(subset="resposta_id")
    print(f"[integridade] {n_ruins} linha(s) malformada(s) e {n_dup} duplicata(s) fora")
    print(f"[corpus de respostas] {len(val):,} respostas em "
          f"{val.tweet_pai.nunique():,} publicações")
    print("   declarado na 3.6.3: 48.124 respostas, 2.407 publicações\n")

    val["texto"] = val.texto.fillna("").astype(str)
    print("[valência] mesmo classificador da etapa 2")
    probs = classificar_valencia(list(zip(val.resposta_id, val.texto)), CACHE)
    val["p_pos"] = val.resposta_id.map(lambda i: probs[i][0])
    val["p_neg"] = val.resposta_id.map(lambda i: probs[i][1])
    val["p_neu"] = val.resposta_id.map(lambda i: probs[i][2])
    val["intensidade"] = 1 - val.p_neu
    val["assimetria"] = val.p_neg - val.p_pos

    print("\n[moral] mesmo dicionário da etapa 2")
    exatos, prefixos = carregar_mfd()
    med = pd.DataFrame([medir_moral(t, exatos, prefixos) for t in val.texto],
                       index=val.index)
    val = pd.concat([val, med], axis=1)
    val["tem_moral"] = (val.n_moral > 0).astype(int)

    print(f"   mediana de tokens após limpeza: {val.n_tokens.median():.0f}")
    print(f"   com cinco tokens ou menos: {100 * (val.n_tokens <= 5).mean():.1f}%")
    print(f"   contêm termo moral: {100 * val.tem_moral.mean():.1f}%")
    print(f"   assimetria média das respostas: {val.assimetria.mean():+.3f}")
    print("   declarado: mediana 6 tokens, 46% com cinco ou menos, "
          "19,8% morais, assimetria +0,274\n")

    val.to_csv(SAIDA, index=False, encoding="utf-8")
    print(f"gravado: respostas_classificadas.csv  ({len(val):,} linhas)")


if __name__ == "__main__":
    main()
