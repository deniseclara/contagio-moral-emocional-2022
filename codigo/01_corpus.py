# -*- coding: utf-8 -*-
"""
ETAPA 1 — Constituição do corpus (seção 3.2 da dissertação).

Entra com a tabela de chaves do ITED-Br e o conteúdo recuperado das três contas.
Aplica, nesta ordem, os filtros descritos na seção 3.2:

  1. janela de campanha, de 16/08 a 30/10/2022, sobre a DATA DE PARTIÇÃO do
     ITED-Br. Não é o carimbo de tempo do tweet. Filtrar pelo carimbo devolve
     3.506 publicações em lugar de 3.546.
  2. junção com o conteúdo recuperado. Falha quando a coluna de erro está
     preenchida ou quando a publicação voltou sem endereço.
  3. restrição à unidade de análise: publicações originais, isto é, aquelas sem
     tweet referenciado. Exclui as continuações de sequência, que herdam a
     audiência da publicação que abriu a série.

Reproduz a Tabela 1: 3.546 identificadores, 3.515 recuperados, 2.717 originais.

Saídas
  dados/derivados/corpus.csv           unidade de análise, N = 2.717
  dados/derivados/corpus_completo.csv  com as continuações, para a robustez
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from comum import BRUTOS, DERIVADOS, JANELA_INI, JANELA_FIM, CANDIDATOS

_RE_NUM = re.compile(r"([\d.,]+)\s*([KMkm])?")


def para_inteiro(valor):
    """Converte o rótulo de acessibilidade da interface em número inteiro.

    A recuperação guardou o texto que a plataforma expõe a leitores de tela,
    do tipo '12596 Likes. Like' ou '535.2K Views'. O sufixo K multiplica por
    mil e o M por um milhão.
    """
    if pd.isna(valor):
        return 0
    m = _RE_NUM.search(str(valor).replace(" ", " "))
    if not m:
        return 0
    n = m.group(1)
    # 535.2K usa ponto decimal; 12.596 usa ponto de milhar
    n = n.replace(",", ".") if m.group(2) else n.replace(".", "").replace(",", "")
    try:
        x = float(n)
    except ValueError:
        return 0
    s = (m.group(2) or "").upper()
    return int(x * (1000 if s == "K" else 1_000_000 if s == "M" else 1))


def main():
    ch = pd.read_csv(os.path.join(BRUTOS, "ited_chaves.csv"),
                     dtype={"id": str, "referenced_tweet_id": str,
                            "conversation_id": str})
    print(f"[ITED-Br] {len(ch):,} identificadores na tabela de chaves")

    jan = ch[ch.data_ited.between(JANELA_INI, JANELA_FIM)].copy()
    print(f"[JANELA]  {JANELA_INI} a {JANELA_FIM}: {len(jan):,}")

    hidr = pd.concat([pd.read_csv(os.path.join(BRUTOS, "candidatos", f"{c}.csv"),
                                  dtype={"id": str}) for c in CANDIDATOS],
                     ignore_index=True)
    assert hidr["id"].is_unique, "identificadores repetidos no conteúdo recuperado"

    df = jan.merge(hidr.drop(columns=["autor_nome"]), on="id", how="left")
    falhou = df["erro"].notna() | df["url"].isna()
    print(f"[FALHAS]  {falhou.sum()} publicações não recuperadas")
    df = df[~falhou].copy()
    print(f"[RECUPERADOS] {len(df):,} ({len(df) / len(jan) * 100:.1f}%)")

    for origem, destino in [("retweets", "rt"), ("curtidas", "likes"),
                            ("respostas", "replies"), ("visualizacoes", "views")]:
        df[destino] = df[origem].map(para_inteiro)

    df["dia"] = df["data_ited"]
    df["data_pub"] = pd.to_datetime(df["data"], utc=True, errors="coerce") \
                       .dt.tz_convert("America/Sao_Paulo")
    df["texto"] = df["texto"].fillna("").astype(str).str.strip()
    df["sem_texto"] = df["texto"].str.len() == 0

    cols = ["id", "candidato", "data_ited", "dia", "data_pub", "texto",
            "sem_texto", "rt", "likes", "replies", "views",
            "referenced_tweet_id", "conversation_id"]
    completo = df[cols].copy()
    primario = completo[completo.referenced_tweet_id.isna()].copy()

    completo.to_csv(os.path.join(DERIVADOS, "corpus_completo.csv"),
                    index=False, encoding="utf-8")
    primario.to_csv(os.path.join(DERIVADOS, "corpus.csv"),
                    index=False, encoding="utf-8")

    print(f"\n[UNIDADE DE ANÁLISE] {len(primario):,} publicações originais")
    print(primario.candidato.value_counts().to_string())
    n = int(primario.sem_texto.sum())
    print(f"\n{n} publicação(ões) recuperada(s) só com mídia, sem texto. "
          f"Entra(m) na Tabela 1 e sai(em) da classificação, "
          f"o que leva o N efetivo dos modelos a {len(primario) - n:,}.")
    print(f"\ncorpus completo, com continuações: {len(completo):,}")
    print("\nDeclarado na Tabela 1: 3.546 / 3.515 / 2.717 "
          "— Lula 1.606, Bolsonaro 291, Ciro 820")


if __name__ == "__main__":
    main()
