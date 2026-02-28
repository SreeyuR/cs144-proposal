import pandas as pd
import networkx as nx
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt

def get_seller_graph():
    sellers = pd.read_csv("sellers.csv")
    tags = pd.read_csv("seller_tags.csv")

    # 1) tag sets
    tag_sets = tags.groupby("seller_id")["tag"].apply(set).to_dict()

    # 2) seller metadata
    seller_meta = sellers.set_index("seller_id").to_dict(orient="index")

    # Ensure every seller has a tag set (even empty) so we don't KeyError
    for sid in seller_meta.keys():
        tag_sets.setdefault(sid, set())

    seller_ids = list(seller_meta.keys())

    # --- Type affinity buckets (POC-friendly) ---
    # Map fine-grained seller_type -> broader family
    TYPE_FAMILY = {
        "thrift_store": "thrift",
        "consignment_thrift": "curated",
        "resale_store": "curated",
        "vintage_thrift": "vintage",
        "flea_market_vendor": "offline",
        "instagram_only_vendor": "online_micro",
    }

    def family(seller_id: str) -> str:
        stype = seller_meta[seller_id].get("seller_type", "")
        return TYPE_FAMILY.get(stype, "other")

    # Which families should be considered "similar enough" to connect by type?
    # (You can tweak these to get a graph that's not too dense.)
    TYPE_SIMILAR = {
        ("curated", "vintage"),
        ("curated", "curated"),
        ("vintage", "vintage"),
        ("thrift", "thrift"),
        # Optional: connect thrift <-> vintage a bit (often adjacent shoppers)
        ("thrift", "vintage"),
    }

    def type_affine(a: str, b: str) -> bool:
        fa, fb = family(a), family(b)
        return (fa, fb) in TYPE_SIMILAR or (fb, fa) in TYPE_SIMILAR

    # --- Edge rule thresholds ---
    T = 2  # shared tag threshold

    def same_area(a: str, b: str) -> bool:
        return seller_meta[a].get("area", "") != "" and seller_meta[a].get("area") == seller_meta[b].get("area")

    def shared_tags_enough(a: str, b: str) -> bool:
        return len(tag_sets[a] & tag_sets[b]) >= T

    # --- Build graph ---
    G = nx.Graph()

    # Add nodes with metadata (useful for later visualization)
    for sid, meta in seller_meta.items():
        G.add_node(sid, **meta)

    # Add edges via OR-rule
    for i in range(len(seller_ids)):
        for j in range(i + 1, len(seller_ids)):
            a, b = seller_ids[i], seller_ids[j]

            if shared_tags_enough(a, b) or same_area(a, b) or type_affine(a, b):
                # Store *why* the edge exists as an attribute (still unweighted)
                reasons = []
                if shared_tags_enough(a, b):
                    reasons.append(f"shared_tags>={T}")
                if same_area(a, b):
                    reasons.append("same_area")
                if type_affine(a, b):
                    reasons.append(f"type_affinity:{family(a)}~{family(b)}")
                G.add_edge(a, b, reasons=";".join(reasons))

    # bridges for offline gems / social discovery
    G.add_edge("s03", "s07", reasons="manual_bridge:treasure_hunt_to_flea")
    G.add_edge("s07", "s08", reasons="manual_bridge:same_flea_market")
    G.add_edge("s06", "s09", reasons="manual_bridge:alt_to_ig_vendor")

    print("Nodes:", G.number_of_nodes())
    print("Edges:", G.number_of_edges())
    print("Connected components:", nx.number_connected_components(G))
    return G

def plot_seller_graph(
    G: nx.Graph,
    *,
    title: str = "ThriftNet Seller Graph",
    seed: int = 7,
    with_labels: bool = True,
    label_attr: str = "name",
    figsize=(12, 9),
):
    """
    Pretty-ish NetworkX plot:
      - Node color by seller 'family' (derived from node attr 'seller_type')
      - Node size by degree
      - Labels use node attribute 'name' if present (fallback to node id)
      - Uses spring layout for readability
    """
    # --- helper: map seller_type -> family (same mapping as earlier) ---
    TYPE_FAMILY = {
        "thrift_store": "thrift",
        "consignment_thrift": "curated",
        "resale_store": "curated",
        "vintage_thrift": "vintage",
        "flea_market_vendor": "offline",
        "instagram_only_vendor": "online_micro",
    }

    def family(n):
        stype = G.nodes[n].get("seller_type", "")
        return TYPE_FAMILY.get(stype, "other")

    families = [family(n) for n in G.nodes()]
    fam_list = sorted(set(families))
    fam_to_idx = {f: i for i, f in enumerate(fam_list)}
    node_color_vals = [fam_to_idx[family(n)] for n in G.nodes()]

    # Node sizes based on degree (bounded for aesthetics)
    degrees = dict(G.degree())
    node_sizes = [250 + 140 * min(degrees[n], 10) for n in G.nodes()]

    # Labels
    if with_labels:
        labels = {}
        for n in G.nodes():
            nm = G.nodes[n].get(label_attr, n)
            # keep labels short-ish to reduce clutter
            if isinstance(nm, str) and len(nm) > 22:
                nm = nm[:21] + "…"
            labels[n] = nm
    else:
        labels = None

    # Layout
    pos = nx.spring_layout(G, seed=seed, k=None)  # k auto; tweak if needed

    # Plot
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_title(title, fontsize=14)

    # Edges
    nx.draw_networkx_edges(
        G, pos,
        ax=ax,
        width=1.0,
        alpha=0.25,
        edge_color="0.3"
    )

    # Nodes (use a categorical colormap without hardcoding specific colors)
    nodes = nx.draw_networkx_nodes(
        G, pos,
        ax=ax,
        node_size=node_sizes,
        node_color=node_color_vals,
        cmap=plt.cm.Set3,
        linewidths=0.8,
        edgecolors="0.2",
        alpha=0.95
    )

    # Labels
    if with_labels and labels is not None:
        nx.draw_networkx_labels(
            G, pos,
            labels=labels,
            font_size=9,
            font_color="0.1",
            ax=ax
        )

    # Legend (match colormap)
    cmap = plt.cm.Set3
    handles = []
    for f in fam_list:
        idx = fam_to_idx[f]
        handles.append(
            Line2D(
                [0], [0],
                marker="o",
                linestyle="",
                markersize=10,
                markerfacecolor=cmap(idx / max(1, len(fam_list) - 1)),
                markeredgecolor="0.2",
                label=f
            )
        )
    ax.legend(handles=handles, title="Seller family", loc="best", frameon=True)

    ax.axis("off")
    plt.tight_layout()
    plt.savefig("seller_graph.png")

plot_seller_graph(get_seller_graph())


if __name__ == "__main__":
    G = get_seller_graph()
    print("Graph stats:")
    print("Number of nodes:", G.number_of_nodes())
    print("Number of edges:", G.number_of_edges())
    print("Number of connected components:", nx.number_connected_components(G))

    # BFS for hidden gem discovery
    source = "s01"  # Revival
    target = "s07"  # Rose Bowl handbag vendor

    path = nx.shortest_path(G, source=source, target=target)  # BFS since unweighted
    print("Discovery path:", path)

    # recommend “stores near what you like” (neighborhood expansion)
    seed = "s06"  # MeowMeowz
    neighbors = list(G.neighbors(seed))
    print("Similar/adjacent sellers:", neighbors)

    # Connected components / clusters
    components = list(nx.connected_components(G))
    print("Number of components:", len(components))
    print("Largest component size:", max(len(c) for c in components))