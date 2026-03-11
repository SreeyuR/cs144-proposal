# CS 144 pdf crawler for Epstein Files

import csv
import itertools
import re
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
from pypdf import PdfReader


def load_exclude_words(csv_path: Path) -> set[str]:
    exclude = set()
    with open(csv_path, newline="", encoding="utf-8", errors="ignore") as f:
        for row in csv.DictReader(f):
            w = row.get("word", "").strip()
            if w:
                exclude.add(w.lower())
    return exclude


def load_first_names(csv_path: Path, name_column: str = "Child's First Name") -> set[str]:
    first_names = set()
    with open(csv_path, newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        if name_column not in reader.fieldnames:
            raise ValueError(f"Column '{name_column}' not found. Available: {reader.fieldnames}")
        for row in reader:
            name = row.get(name_column, "").strip()
            if name and name.isalpha() and len(name) > 1:
                first_names.add(name.lower())
    return first_names


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def find_names(text: str, first_names: set[str], exclude_words=None) -> set[str]:
    exclude_words = exclude_words or set()
    pattern = re.compile(r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b")

    candidates = set()
    for match in pattern.finditer(text):
        first, last = match.group(1), match.group(2)
        if first.lower() in exclude_words or last.lower() in exclude_words:
            continue
        if first.lower() in first_names:
            candidates.add(f"{first} {last}")

    return candidates


def extract_names_from_pdf(pdf_name: str, verbose: bool = True) -> list[str]:
    folder = Path(__file__).parent
    pdf_path = Path(pdf_name) if Path(pdf_name).is_absolute() else folder / pdf_name
    names_csv_path = folder / "Popular_Baby_Names.csv"
    exclude_csv_path = folder / "exclude_words.csv"

    if not names_csv_path.exists():
        raise FileNotFoundError(f"Baby names CSV not found: {names_csv_path}")

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    first_names = load_first_names(names_csv_path)
    exclude_words = load_exclude_words(exclude_csv_path) if exclude_csv_path.exists() else set()
    text = extract_text_from_pdf(str(pdf_path))

    names = find_names(text, first_names, exclude_words)
    return sorted(names)


def visualize_graph(graph: nx.Graph, output_path: Path) -> None:
    plt.figure(figsize=(20, 16), facecolor="white")
    pos = nx.spring_layout(graph, seed=42, k=1.2, iterations=80)
    
    node_colors = ["#e74c3c" if n == "Jeffrey Epstein" else "#3498db" for n in graph.nodes()]
    node_sizes = [400 if n == "Jeffrey Epstein" else 200 for n in graph.nodes()]
    
    nx.draw_networkx_edges(graph, pos, edge_color="#4a5568", width=0.5, alpha=0.7)
    nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=node_sizes, alpha=0.9)
    nx.draw_networkx_labels(graph, pos, font_size=15, font_weight="bold")
    
    plt.title("Name co-occurrence network (names appearing in same PDF)", fontsize=14)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    folder = Path(__file__).parent
    files_folder = folder / "files"
    pdf_files = sorted(files_folder.glob("*.pdf"))

    list_of_lists = []
    for pdf_path in pdf_files:
        names = extract_names_from_pdf(str(pdf_path), verbose=False)
        list_of_lists.append(names)

    graph = nx.Graph()
    for names in list_of_lists:
        for name in names:
            graph.add_node(name)
        for a, b in itertools.combinations(names, 2):
            graph.add_edge(a, b)

    graph.add_node("Jeffrey Epstein")
    for node in graph.nodes():
        if node != "Jeffrey Epstein":
            graph.add_edge("Jeffrey Epstein", node)

    print(f"Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

    visualize_graph(graph, folder / "name_network.png")
