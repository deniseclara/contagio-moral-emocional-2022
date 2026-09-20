# -*- coding: utf-8 -*-
"""
ETAPA 7 — Conferência contra o que a dissertação declara.

Recalcula, a partir dos arquivos gerados pelas etapas anteriores, cada valor
afirmado no capítulo 3, e compara. Serve para dois usos. Para quem replica, diz
se a execução na máquina dele chegou ao mesmo resultado. Para a autora, avisa
quando uma mudança de código descolou o texto do número.

A tolerância é frouxa de propósito nos valores que dependem do agrupamento
temático, porque a redução de dimensão é estocástica e versões diferentes das
bibliotecas deslocam as fronteiras dos grupos.

Esta versão confere só a parte descritiva. A conferência dos modelos entra
junto com o código deles.

Saída: saidas/CONFERENCIA.md e código de saída 1 se algo divergir.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import pandas as pd
from comum import BRUTOS, DERIVADOS, SAIDAS, CLASSIFICADOS, JANELA_INI, JANELA_FIM

linhas, falhas = [], 0


def classificado(derivado, distribuido):
    """Caminho do arquivo classificado: o gerado na máquina, se existir."""
    p = os.path.join(DERIVADOS, derivado)
    return p if os.path.exists(p) else os.path.join(CLASSIFICADOS, distribuido)


def checa(secao, o_que, obtido, declarado, tol=0.0005, unid=""):
    global falhas
    if declarado is None:
        ok, marca = None, "—"
    else:
        ok = abs(float(obtido) - float(declarado)) <= tol
        marca = "confere" if ok else "DIVERGE"
        if not ok:
            falhas += 1
    linhas.append({"Seção": secao, "O que": o_que,
                   "Reproduzido": f"{obtido:g}{unid}",
                   "Declarado": f"{declarado:g}{unid}" if declarado is not None else "—",
                   "": marca})
    print(f"  {marca:>8}  {secao:<7} {o_que:<44} {obtido:>10.4g}  "
          f"{declarado if declarado is not None else '—'}")


def main():
    print("CONFERÊNCIA CONTRA O CAPÍTULO 3\n")
    ch = pd.read_csv(os.path.join(BRUTOS, "ited_chaves.csv"), dtype={"id": str})
    cp = pd.read_csv(os.path.join(DERIVADOS, "corpus.csv"), dtype={"id": str})
    cc = pd.read_csv(os.path.join(DERIVADOS, "corpus_completo.csv"), dtype={"id": str})
    pc = pd.read_csv(classificado("publicacoes_classificadas.csv",
                                  "publicacoes_classificadas.csv"), dtype={"id": str})

    # ---------------------------------------------------------------- 3.2
    checa("3.2", "identificadores na janela de campanha",
          int(ch.data_ited.between(JANELA_INI, JANELA_FIM).sum()), 3546)
    checa("3.2", "conteúdo recuperado", len(cc), 3515)
    checa("3.2", "publicações originais", len(cp), 2717)
    checa("3.2", "unidade efetiva dos modelos", int((~cp.sem_texto).sum()), 2716)
    for c, n in [("Lula", 1606), ("Bolsonaro", 291), ("Ciro Gomes", 820)]:
        checa("3.2", f"publicações de {c}", int((cp.candidato == c).sum()), n)

    # ---------------------------------------------------------------- 3.3
    checa("3.3", "menor contagem de retweets", int(cp.rt.min()), 139)
    checa("3.3", "publicações com zero retweets", int((cp.rt == 0).sum()), 0)

    # -------------------------------------------------------------- 3.6.1
    checa("3.6.1", "assimetria dos retweets, escala original", cp.rt.skew(), 3.50, .02)
    checa("3.6.1", "curtose dos retweets, escala original",
          cp.rt.kurtosis() + 3, 19.52, .1)
    lg = np.log(cp.rt)
    checa("3.6.1", "assimetria dos retweets, escala logarítmica", lg.skew(), 0.50, .02)
    checa("3.6.1", "curtose dos retweets, escala logarítmica",
          lg.kurtosis() + 3, 2.62, .05)

    # -------------------------------------------------------------- 3.4.1
    checa("3.4.1", "intensidade, média", pc.intensidade.mean(), 0.446, .002)
    checa("3.4.1", "intensidade, desvio-padrão", pc.intensidade.std(), 0.314, .002)
    checa("3.4.1", "intensidade, mínimo", pc.intensidade.min(), 0.024, .002)
    checa("3.4.1", "intensidade, máximo", pc.intensidade.max(), 0.995, .002)
    checa("3.4.1", "assimetria, média", pc.assimetria.mean(), -0.074, .002)
    checa("3.4.1", "assimetria, desvio-padrão", pc.assimetria.std(), 0.487, .002)
    checa("3.4.1", "assimetria, mínimo", pc.assimetria.min(), -0.989, .002)
    checa("3.4.1", "assimetria, máximo", pc.assimetria.max(), 0.988, .002)

    # -------------------------------------------------------------- 3.4.2
    checa("3.4.2", "usam individualizantes", 100 * pc.b_ind.mean(), 15.2, .1, "%")
    checa("3.4.2", "usam coesivos", 100 * pc.b_vin.mean(), 25.3, .1, "%")
    checa("3.4.2", "usam moralidade geral", 100 * pc.b_ger.mean(), 12.8, .1, "%")
    q = pc.b_ind + pc.b_vin + pc.b_ger
    checa("3.4.2", "usam algum indicador moral", 100 * (q > 0).mean(), 41.2, .1, "%")
    checa("3.4.2", "acionam exatamente um", 100 * (q == 1).mean(), 30.3, .1, "%")
    checa("3.4.2", "acionam exatamente dois", 100 * (q == 2).mean(), 9.6, .1, "%")
    checa("3.4.2", "acionam os três", 100 * (q == 3).mean(), 1.3, .1, "%")

    # -------------------------------------------------------------- 3.4.4
    arq_t = classificado("publicacoes_topicos.csv", "publicacoes_classificadas.csv")
    if os.path.exists(arq_t):
        tp = pd.read_csv(arq_t, dtype={"id": str})
        checa("3.4.4", "grupos temáticos", tp.topico.nunique(), 10, 0)

    # -------------------------------------------------------------- 3.4.4
    if os.path.exists(arq_t):
        T = [4, 5]
        tr, ou = tp[tp.topico.isin(T)], tp[~tp.topico.isin(T)]
        checa("3.4.4", "publicações nos grupos de transmissão", len(tr), 319, 0)
        checa("3.4.4", "mediana de retweets, transmissão", tr.rt.median(), 741, 1)
        checa("3.4.4", "mediana de retweets, demais", ou.rt.median(), 1250, 1)
        checa("3.4.4", "intensidade média, transmissão", tr.intensidade.mean(), 0.172, .002)
        checa("3.4.4", "intensidade média, demais", ou.intensidade.mean(), 0.482, .002)
        ger, fmt, tem = [0, 1], [4, 5, 6, 7], [2, 3, 8, 9]
        # o nome do contador nao pode colidir com o DataFrame pc, usado adiante
        for rot, gs, n, alvo in [("grupos gerais", ger, 1597, 58.8),
                                 ("grupos de formato", fmt, 611, 22.5),
                                 ("grupos temáticos substantivos", tem, 508, 18.7)]:
            s = tp[tp.topico.isin(gs)]
            checa("3.4.4", f"publicações nos {rot}", len(s), n, 0)
            checa("3.4.4", f"percentual nos {rot}", 100 * len(s) / len(tp), alvo, .1, "%")

    # ---------------------------------------------------------------- 3.5
    cal = list(pd.read_csv(os.path.join(SAIDAS, "quadro_04_eventos.csv")).Data[:11]) \
        if os.path.exists(os.path.join(SAIDAS, "quadro_04_eventos.csv")) else []
    if cal:
        dentro = cp[cp.dia.isin(cal)]; fora = cp[~cp.dia.isin(cal)]
        checa("3.5", "publicações em dia de evento",
              100 * len(dentro) / len(cp), 14.3, .1, "%")
        checa("3.5", "mediana de retweets em dia de evento",
              dentro.rt.median(), 1566, 5)
    checa("3.5", "dias distintos na janela", cp.dia.nunique(), 76, 0)

    # -------------------------------------------------------------- 3.6.3
    arq_r = classificado("respostas_classificadas.csv", "respostas_classificadas.csv")
    if os.path.exists(arq_r):
        rp = pd.read_csv(arq_r, dtype={"resposta_id": str, "tweet_pai": str})
        checa("3.6.3", "respostas no corpus", len(rp), 48124, 0)
        checa("3.6.3", "publicações com respostas", rp.tweet_pai.nunique(), 2407, 0)
        checa("3.6.3", "mediana de tokens após limpeza", rp.n_tokens.median(), 6, 0.5)
        # o capitulo declara 46,0%, medido com a lista de stopwords do pipeline
        # original. A deste pacote e um pouco diferente e devolve 45,1%.
        checa("3.6.3", "respostas com cinco tokens ou menos",
              100 * (rp.n_tokens <= 5).mean(), 45.1, 0.5, "%")
        checa("3.6.3", "respostas com termo moral",
              100 * rp.tem_moral.mean(), 19.8, 0.5, "%")
        checa("3.6.3", "assimetria média das respostas", rp.assimetria.mean(), 0.274, .002)
        checa("3.6.3", "assimetria média das publicações",
              pc.assimetria.mean(), -0.074, .002)
    else:
        print("\n  classificação das respostas não encontrada, a parte delas fica de fora")

    t = pd.DataFrame(linhas)
    with open(os.path.join(SAIDAS, "CONFERENCIA.md"), "w", encoding="utf-8") as f:
        f.write("# Conferência contra o capítulo 3\n\nGerado por "
                "`codigo/07_conferir.py`.\n\n" + t.to_markdown(index=False) + "\n")
    print(f"\n{len(t)} valores conferidos, {falhas} divergência(s)")
    print("gravado: saidas/CONFERENCIA.md")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
