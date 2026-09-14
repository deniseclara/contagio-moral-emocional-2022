# -*- coding: utf-8 -*-
"""
ETAPA 3 — Dimensão temática (seção 3.4.4).

Os assuntos não foram definidos por uma lista prévia de categorias. Emergem de
um agrupamento automático que reúne publicações de vocabulário semelhante,
executado com o BERTopic (GROOTENDORST, 2022). O procedimento converte cada
texto em uma representação numérica que preserva similaridade de sentido, reduz
a dimensão dessa representação, agrupa as parecidas e extrai as palavras que
melhor distinguem cada grupo.

O resultado entra nos modelos como controle, e não como objeto de interpretação
substantiva. A seção 3.4.4 registra que cinco dos treze grupos correspondem a
formato de publicação, e não a tema.

REPRODUTIBILIDADE
A redução de dimensão é estocástica. Sem semente fixa, duas execuções devolvem
agrupamentos diferentes. A semente está fixada abaixo. Ainda assim, versões
diferentes das bibliotecas podem deslocar as fronteiras dos grupos, então o
arquivo do modelo treinado é gravado junto, em dados/derivados/_bertopic.

Saída: dados/derivados/publicacoes_topicos.csv
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import pandas as pd
from comum import DERIVADOS, STOPWORDS, limpar_para_topicos

SEMENTE = 42
ENTRADA = os.path.join(DERIVADOS, "publicacoes_classificadas.csv")
SAIDA = os.path.join(DERIVADOS, "publicacoes_topicos.csv")
MODELO = os.path.join(DERIVADOS, "_bertopic")


def main():
    df = pd.read_csv(ENTRADA, dtype={"id": str})
    print(f"[corpus] {len(df):,} publicações")
    docs = [limpar_para_topicos(t) for t in df.texto]

    from bertopic import BERTopic
    from bertopic.vectorizers import ClassTfidfTransformer
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP
    from hdbscan import HDBSCAN

    print("[3.4.4] gerando as representações numéricas ...")
    emb_modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    emb = emb_modelo.encode(docs, show_progress_bar=False, batch_size=64)

    umap = UMAP(n_neighbors=15, n_components=5, min_dist=0.0,
                metric="cosine", random_state=SEMENTE)
    hdb = HDBSCAN(min_cluster_size=25, metric="euclidean",
                  cluster_selection_method="eom", prediction_data=True)
    vect = CountVectorizer(stop_words=list(STOPWORDS), ngram_range=(1, 2), min_df=3)

    print("[3.4.4] agrupando ...")
    modelo = BERTopic(embedding_model=emb_modelo, umap_model=umap,
                      hdbscan_model=hdb, vectorizer_model=vect,
                      ctfidf_model=ClassTfidfTransformer(reduce_frequent_words=True),
                      calculate_probabilities=False, verbose=False)
    topicos, _ = modelo.fit_transform(docs, emb)

    fora = int((np.array(topicos) == -1).sum())
    print(f"   grupos brutos: {len(set(topicos)) - (1 if fora else 0)} | "
          f"sem atribuição: {fora} ({100 * fora / len(docs):.1f}%)")

    # todo documento precisa de um grupo, porque o tema entra como agrupamento
    # no modelo. Os deixados de fora são realocados pela representação numérica.
    if fora:
        topicos = modelo.reduce_outliers(docs, topicos, strategy="embeddings",
                                         embeddings=emb)
        modelo.update_topics(docs, topics=topicos, vectorizer_model=vect)
        print(f"   após realocação: {len(set(topicos))} grupos, "
              f"{int((np.array(topicos) == -1).sum())} sem atribuição")

    modelo.save(MODELO, serialization="safetensors", save_ctfidf=True,
                save_embedding_model=False)

    df["topico"] = topicos
    info = modelo.get_topic_info()
    rot = {r["Topic"]: ", ".join(p[0] for p in (modelo.get_topic(r["Topic"]) or [])[:5])
           for _, r in info.iterrows()}
    df["topico_rotulo"] = df.topico.map(rot)
    df.to_csv(SAIDA, index=False, encoding="utf-8")

    print(f"\n[grupos] {df.topico.nunique()} (declarado na 3.4.4: 13)\n")
    t = (df.groupby(["topico", "topico_rotulo"])
           .agg(publicacoes=("id", "size"), rt_mediana=("rt", "median"))
           .reset_index().sort_values("publicacoes", ascending=False))
    t["pct"] = (100 * t.publicacoes / len(df)).round(1)
    print(t.to_string(index=False, max_colwidth=52))
    print(f"\ngravado: publicacoes_topicos.csv ({len(df):,} linhas)")


if __name__ == "__main__":
    main()
