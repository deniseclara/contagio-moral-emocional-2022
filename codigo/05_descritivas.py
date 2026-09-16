# -*- coding: utf-8 -*-
"""
ETAPA 5 — Tabelas e quadros descritivos do capítulo 3.

Gera, em saidas/DESCRITIVAS.md e em arquivos csv separados:

  Tabela 1  construção do corpus                       (3.2)
  Tabela 2  engajamento por candidato                  (3.3)
  Tabela 3  fundamentos morais nas publicações         (3.4.3)
  Tabela 4  fundamentos morais nas respostas           (3.4.3)
  Quadro 3  os dez grupos temáticos                    (3.4.4)
  Quadro 4  datas de maior repercussão                 (3.5)

A numeração segue o capítulo 3 revisado em 16/09/2026, em que as antigas Tabelas
2 e 3 viraram uma só e os quadros passaram a ser numerados de 1 a 5.

Lê a classificação de dados/derivados/ quando as etapas 2 a 4 foram executadas
e, se não foram, a que acompanha o repositório em dados/classificados/.

Saída: saidas/DESCRITIVAS.md e saidas/tabela_*.csv
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import pandas as pd
from comum import (BRUTOS, DERIVADOS, SAIDAS, CLASSIFICADOS, CANDIDATOS,
                   CATEGORIAS, JANELA_INI, JANELA_FIM)

ORDEM = ["Lula", "Bolsonaro", "Ciro Gomes"]
EVENTOS = {
 "2022-08-16": "início da propaganda eleitoral",
 "2022-08-26": "início da propaganda eleitoral gratuita no rádio e na televisão (1º turno)",
 "2022-08-28": "primeiro debate presidencial, em pool Band/Cultura/UOL/Folha",
 "2022-09-07": "atos do 7 de setembro",
 "2022-09-24": "debate em pool SBT/CNN Brasil/Estadão/Veja/NovaBrasil FM/Terra",
 "2022-09-29": "debate da Globo, último antes do 1º turno",
 "2022-10-02": "votação do primeiro turno",
 "2022-10-07": "início da campanha do segundo turno",
 "2022-10-16": "primeiro debate Lula × Bolsonaro no 2º turno, em pool Band/Cultura/Folha/UOL/CNN",
 "2022-10-28": "debate da Globo, último encontro televisivo antes da votação",
 "2022-10-30": "votação do segundo turno"}


def classificado(derivado, distribuido):
    """Caminho do arquivo classificado: o gerado na máquina, se existir."""
    p = os.path.join(DERIVADOS, derivado)
    return p if os.path.exists(p) else os.path.join(CLASSIFICADOS, distribuido)

FUND = ["cuidado", "justica", "lealdade", "autoridade", "santidade"]
partes = []


def bloco(titulo, tabela, nota="", arquivo=None):
    partes.append(f"\n## {titulo}\n\n{tabela.to_markdown(index=False)}\n")
    if nota:
        partes.append(f"\n{nota}\n")
    if arquivo:
        tabela.to_csv(os.path.join(SAIDAS, arquivo), index=False, encoding="utf-8")
    print(f"\n{titulo}\n{tabela.to_string(index=False)}")


def main():
    ch = pd.read_csv(os.path.join(BRUTOS, "ited_chaves.csv"), dtype={"id": str})
    cp = pd.read_csv(os.path.join(DERIVADOS, "corpus.csv"), dtype={"id": str})
    tp = pd.read_csv(classificado("publicacoes_topicos.csv",
                                  "publicacoes_classificadas.csv"), dtype={"id": str})
    tp["candidato"] = pd.Categorical(tp.candidato, ORDEM, ordered=True)

    # ------------------------------------------------------------- Tabela 1
    jan = ch[ch.data_ited.between(JANELA_INI, JANELA_FIM)]
    t1 = pd.DataFrame({
        "Etapa": ["Identificadores no ITED-Br, na janela de campanha",
                  "Conteúdo recuperado",
                  "Publicações originais",
                  "Com texto, unidade efetiva dos modelos"],
        "Publicações": [len(jan), len(pd.read_csv(os.path.join(DERIVADOS,
                        "corpus_completo.csv"), dtype={"id": str})),
                        len(cp), int((~cp.sem_texto).sum())]})
    bloco("Tabela 1 — Construção do corpus", t1,
          "Fonte: elaboração própria a partir do ITED-Br (IASULAITIS et al., 2025).",
          "tabela_01_corpus.csv")

    # ------------------------------------------------------------- Tabela 2
    # Uma tabela só, por candidato e no total, sobre as publicações com texto
    # (a unidade dos modelos). Sem quartis. A mediana fica ao lado da média
    # porque a distribuição do engajamento é muito assimétrica.
    ct = cp[~cp.sem_texto]
    linhas2 = []
    for medida, col in [("Retweets", "rt"), ("Curtidas", "likes"), ("Respostas", "replies")]:
        for i, c in enumerate(ORDEM + ["Total"]):
            s = ct[col] if c == "Total" else ct[ct.candidato == c][col]
            linhas2.append({"Medida": medida if i == 0 else "", "Candidato": c,
                            "Média": int(round(s.mean())), "Desvio-padrão": int(round(s.std())),
                            "Mediana": int(round(s.median())), "Mín.": int(s.min()),
                            "Máx.": int(s.max())})
    bloco("Tabela 2 — Engajamento das publicações por candidato", pd.DataFrame(linhas2),
          f"Fonte: elaboração própria. N = {len(ct):,} publicações.",
          "tabela_02_engajamento.csv")

    lg = np.log(cp.rt)
    partes.append(f"\nAssimetria e curtose dos retweets: {cp.rt.skew():.2f} e "
                  f"{cp.rt.kurtosis() + 3:.2f} na escala original, "
                  f"{lg.skew():.2f} e {lg.kurtosis() + 3:.2f} na escala "
                  f"logarítmica. Declarado na 3.6.1: assimetria 3,50 e 0,50.\n")

    # ------------------------------------------------------- Tabelas 4 e 5
    def repertorio(d, rot):
        linhas = []
        for c in ORDEM:
            s = d[d.candidato == c]
            l = {"Candidato": c, "N": len(s)}
            for f in FUND:
                col = [f"mfd_{f}_virtude", f"mfd_{f}_vicio"]
                l[f.capitalize()] = round(100 * (s[col].sum(axis=1) > 0).mean(), 1)
            l["Mor. geral"] = round(100 * (s.mfd_moralidade_geral > 0).mean(), 1)
            linhas.append(l)
        return pd.DataFrame(linhas)

    bloco("Tabela 3 — Fundamentos morais nas publicações dos candidatos",
          repertorio(tp, "publicações"),
          "Fonte: elaboração própria. Percentual das publicações que trazem ao "
          "menos um termo do fundamento.", "tabela_03_fundamentos_publicacoes.csv")

    arq_r = classificado("respostas_classificadas.csv", "respostas_classificadas.csv")
    if os.path.exists(arq_r):
        rp = pd.read_csv(arq_r, dtype={"resposta_id": str, "tweet_pai": str})
        rp["candidato"] = pd.Categorical(rp.candidato, ORDEM, ordered=True)
        t5 = repertorio(rp, "respostas").rename(columns={"Candidato": "Candidato do tweet"})
        bloco("Tabela 4 — Fundamentos morais nas respostas recebidas", t5,
              "Fonte: elaboração própria.", "tabela_04_fundamentos_respostas.csv")
    else:
        partes.append("\n## Tabela 4\n\nNão encontrei a classificação das "
                      "respostas. Ver o README.\n")

    # ------------------------------------------------------------- Quadro 6
    q6 = (tp.groupby(["topico", "topico_rotulo"])
            .agg(Publicações=("id", "size"), **{"Retweets (mediana)": ("rt", "median")})
            .reset_index().sort_values("Publicações", ascending=False))
    q6["%"] = (100 * q6.Publicações / len(tp)).round(1)
    q6 = q6.rename(columns={"topico": "Grupo", "topico_rotulo": "Termos que o distinguem"})
    q6["Retweets (mediana)"] = q6["Retweets (mediana)"].astype(int)
    bloco("Quadro 3 — Os grupos identificados no corpus",
          q6[["Grupo", "Termos que o distinguem", "Publicações", "%", "Retweets (mediana)"]],
          "Fonte: elaboração própria.", "quadro_03_topicos.csv")

    # ------------------------------------------------------------- Quadro 7
    linhas = []
    for d, nome in EVENTOS.items():
        s = cp[cp.dia == d]
        linhas.append({"Data": d, "Evento": nome, "Publicações": len(s),
                       "Retweets (mediana)": int(s.rt.median()) if len(s) else 0})
    fora = cp[~cp.dia.isin(EVENTOS)]
    linhas.append({"Data": "demais dias", "Evento": "sem evento de calendário",
                   "Publicações": len(fora), "Retweets (mediana)": int(fora.rt.median())})
    q7 = pd.DataFrame(linhas)
    dentro = cp[cp.dia.isin(EVENTOS)]
    bloco("Quadro 4 — Datas de maior repercussão do período", q7,
          f"Fonte: elaboração própria a partir do calendário eleitoral de 2022. "
          f"As onze datas concentram {100 * len(dentro) / len(cp):.1f}% das "
          f"publicações e têm engajamento "
          f"{100 * (dentro.rt.median() / fora.rt.median() - 1):.1f}% superior em "
          f"mediana. Declarado na 3.5: 14,3% e 14,0%.", "quadro_04_eventos.csv")

    cab = ("# Tabelas e quadros descritivos\n\nGerado por `codigo/05_descritivas.py`. "
           "Os valores declarados na dissertação aparecem em nota abaixo de cada "
           "tabela, para comparação direta.\n")
    with open(os.path.join(SAIDAS, "DESCRITIVAS.md"), "w", encoding="utf-8") as f:
        f.write(cab + "".join(partes))
    print(f"\n\ngravado: saidas/DESCRITIVAS.md")


if __name__ == "__main__":
    main()
