from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "chamados_ti.csv"
OUTPUT_DIR = BASE_DIR / "outputs"
REQUIRED_COLUMNS = {
    "id_chamado",
    "data_abertura",
    "data_fechamento",
    "categoria",
    "prioridade",
    "setor",
    "tecnico",
    "status",
    "sla_horas",
    "satisfacao",
}


def carregar_dados(caminho: Path) -> pd.DataFrame:
    """Carrega o CSV, valida as colunas e converte os tipos principais."""
    df = pd.read_csv(caminho)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {sorted(missing)}")

    df["data_abertura"] = pd.to_datetime(df["data_abertura"], errors="coerce")
    df["data_fechamento"] = pd.to_datetime(df["data_fechamento"], errors="coerce")
    df["sla_horas"] = pd.to_numeric(df["sla_horas"], errors="coerce")
    df["satisfacao"] = pd.to_numeric(df["satisfacao"], errors="coerce")
    return df.drop_duplicates(subset="id_chamado").copy()


def preparar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Cria métricas derivadas utilizadas na análise."""
    df = df.copy()
    delta = df["data_fechamento"] - df["data_abertura"]
    df["tempo_resolucao_horas"] = delta.dt.total_seconds() / 3600
    df["sla_cumprido"] = (
        df["tempo_resolucao_horas"] <= df["sla_horas"]
    ).astype("boolean")
    df.loc[df["data_fechamento"].isna(), "sla_cumprido"] = pd.NA
    df["mes_abertura"] = df["data_abertura"].dt.to_period("M").astype(str)
    return df


def mostrar_indicadores(df: pd.DataFrame) -> None:
    concluidos = df[df["status"].eq("Concluído")]
    percentual_sla = concluidos["sla_cumprido"].mean() * 100

    print("\nANÁLISE DE CHAMADOS DE TI")
    print("-" * 34)
    print(f"Total de chamados: {len(df)}")
    print(f"Chamados concluídos: {len(concluidos)}")
    print(
        "Tempo médio de resolução: "
        f"{concluidos['tempo_resolucao_horas'].mean():.1f} horas"
    )
    print(
        "Mediana do tempo de resolução: "
        f"{concluidos['tempo_resolucao_horas'].median():.1f} horas"
    )
    print(f"Cumprimento do SLA: {percentual_sla:.1f}%")
    print(f"Satisfação média: {concluidos['satisfacao'].mean():.2f}/5")


def gerar_resumos(df: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    resumo = (
        df.groupby("categoria", as_index=False)
        .agg(
            total_chamados=("id_chamado", "count"),
            tempo_medio_horas=("tempo_resolucao_horas", "mean"),
            satisfacao_media=("satisfacao", "mean"),
        )
        .sort_values("total_chamados", ascending=False)
    )
    resumo.to_csv(OUTPUT_DIR / "resumo_por_categoria.csv", index=False)


def gerar_graficos(df: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    sns.set_theme(style="whitegrid", palette="deep")

    plt.figure(figsize=(10, 6))
    ordem = df["categoria"].value_counts().index
    sns.countplot(data=df, y="categoria", order=ordem, color="#2563eb")
    plt.title("Volume de chamados por categoria")
    plt.xlabel("Quantidade")
    plt.ylabel("Categoria")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "chamados_por_categoria.png", dpi=160)
    plt.close()

    concluidos = df[df["status"].eq("Concluído")]
    ordem_prioridade = ["Baixa", "Média", "Alta", "Crítica"]
    plt.figure(figsize=(9, 5))
    sns.barplot(
        data=concluidos,
        x="prioridade",
        y="tempo_resolucao_horas",
        order=ordem_prioridade,
        errorbar=None,
        color="#0f766e",
    )
    plt.title("Tempo médio de resolução por prioridade")
    plt.xlabel("Prioridade")
    plt.ylabel("Horas")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "tempo_por_prioridade.png", dpi=160)
    plt.close()

    sla = concluidos["sla_cumprido"].value_counts().rename(
        index={True: "Cumprido", False: "Não cumprido"}
    )
    plt.figure(figsize=(7, 5))
    sla.plot(kind="bar", color=["#14b8a6", "#f43f5e"])
    plt.title("Cumprimento do SLA")
    plt.xlabel("")
    plt.ylabel("Quantidade de chamados")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "cumprimento_sla.png", dpi=160)
    plt.close()


def main() -> None:
    df = preparar_dados(carregar_dados(DATA_PATH))
    mostrar_indicadores(df)
    gerar_resumos(df)
    gerar_graficos(df)
    print(f"\nArquivos gerados em: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
