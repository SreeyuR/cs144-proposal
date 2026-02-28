import csv
from matplotlib import pyplot as plt
import networkx as nx
import re

def get_user_pairs_from_csv(filepath):
    users = set()
    pairs = []
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            u1 = row["user_id_1"]
            u2 = row["user_id_2"]
            if u1 not in users:
                users.add(u1)
            if u2 not in users:
                users.add(u2)
            pairs.append((u1, u2))

    return users, pairs

def init_users(filepath, G):
    users, pairs = get_user_pairs_from_csv(filepath)

    for user in users:
        G.add_user(user)

    for u1, u2 in pairs:
        print(f"Adding edge between {u1} and {u2}")
        G.add_edge(u1, u2)

def parse_user_seller_csv(filepath):
    edge_list = []
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            edge_list.append({
                "user": row["user_id"],
                "seller": row["seller_id"],
                "edge_id": row["edge_id"],
                "reason": row["reason"]
            })
            
    return edge_list

def _summarize_friend_notes(notes: str) -> str:
    """
    Turn the 'notes' field into a short 1–2 word label for edge annotation.
    Designed for your dataset (thrift/fashion context) and to stay readable on plots.
    """
    if not notes:
        return ""

    t = notes.lower()

    # Domain keyword buckets (ordered by priority)
    # Map many surface forms -> concise label
    patterns = [
        (r"\b(thrift|thrifting|finds|gems|treasure)\b", "Thrift"),
        (r"\b(vintage|denim|boots|handbags|accessories|jewelry)\b", "Vintage"),
        (r"\b(trend|trendy|outfits|fashion)\b", "Trends"),
        (r"\b(style|inspiration|aesthetic)\b", "Style"),
        (r"\b(sustainable|eco)\b", "Eco"),
        (r"\b(home\s*goods|home\s*decor|decor)\b", "Home"),
        (r"\b(formal|professional|interview|work)\b", "Workwear"),
        (r"\b(alt|punk|goth)\b", "Alt"),
        (r"\b(crossover)\b", "Crossover"),
        (r"\b(shop|shopping)\b", "Shop"),
    ]

    hits = []
    for pat, label in patterns:
        if re.search(pat, t):
            hits.append(label)

    # Deduplicate while preserving order
    dedup = []
    for h in hits:
        if h not in dedup:
            dedup.append(h)

    # Prefer 2-word max for readability
    if len(dedup) >= 2:
        return f"{dedup[0]}+{dedup[1]}"
    if len(dedup) == 1:
        return dedup[0]

    # Fallback: extract 1–2 "meaningful" words from notes
    words = re.findall(r"[a-zA-Z]+", t)
    stop = {
        "share","sharing","often","shop","shopping","together","content","with","and","the","a","an",
        "exchange","recommendations","recommendation","overlap"
    }
    words = [w for w in words if w not in stop]
    if not words:
        return ""
    # Take first 2 tokens as a last resort
    if len(words) >= 2:
        return f"{words[0].capitalize()}+{words[1].capitalize()}"
    return words[0].capitalize()


def parse_friendships_csv(filepath):
    """
    Returns:
      users: set[str]
      edges: list[(u1, u2, attrs)]
    attrs includes:
      closeness (float), channel (str), notes (str), short_label (str)
    """
    users = set()
    edges = []
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            u1 = row["user_id_1"]
            u2 = row["user_id_2"]
            users.add(u1)
            users.add(u2)

            channel = (row.get("channel") or "").strip()
            closeness = float(row.get("closeness") or 0.0)
            notes = (row.get("notes") or "").strip()

            short_label = _summarize_friend_notes(notes)

            attrs = {
                "closeness": closeness,
                "channel": channel,
                "notes": notes,
                "short_label": short_label
            }
            edges.append((u1, u2, attrs))

    return users, edges


def pretty_plot_users_only(
    friends_csv_path: str,
    *,
    outpath: str = "users_graph.png",
    title: str = "User Social Graph",
    seed: int = 42,
    figsize=(10, 8),
    show_edge_labels: bool = True,
):
    """
    Builds an undirected user-only graph from friends.csv and saves a PNG.
    - Node size scales with degree
    - Edge width scales with closeness
    - Edge labels are summarized from notes (1–2 word label)
    """
    users, edges = parse_friendships_csv(friends_csv_path)

    UG = nx.Graph()
    for u in users:
        UG.add_node(u, type="user")

    for u1, u2, attrs in edges:
        UG.add_edge(u1, u2, **attrs)

    pos = nx.spring_layout(UG, seed=seed)

    # Node sizes by degree
    deg = dict(UG.degree())
    node_sizes = [700 + 250 * min(deg[n], 8) for n in UG.nodes()]

    # Edge widths by closeness (clamped)
    widths = []
    for u, v in UG.edges():
        c = UG.edges[u, v].get("closeness", 0.0)
        widths.append(1.0 + 3.0 * max(0.0, min(c, 1.0)))  # 1..4

    plt.figure(figsize=figsize)
    ax = plt.gca()
    ax.set_title(title, fontsize=14)

    nx.draw_networkx_edges(
        UG, pos,
        width=widths,
        alpha=0.45,
        edge_color="0.25"
    )

    nx.draw_networkx_nodes(
        UG, pos,
        node_color="skyblue",
        node_size=node_sizes,
        linewidths=1.0,
        edgecolors="0.2",
        alpha=0.95
    )

    nx.draw_networkx_labels(
        UG, pos,
        font_size=10,
        font_color="0.1"
    )

    if show_edge_labels:
        edge_labels = {(u, v): UG.edges[u, v].get("short_label", "") for u, v in UG.edges()}
        nx.draw_networkx_edge_labels(
            UG, pos,
            edge_labels=edge_labels,
            font_size=9,
            font_color="0.15",
            rotate=False,
            label_pos=0.5
        )

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(outpath, dpi=200, bbox_inches="tight")
    plt.close()

    return UG


if __name__ == "__main__":
    UG = pretty_plot_users_only("friends.csv", outpath="users_graph.png")