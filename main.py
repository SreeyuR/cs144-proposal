import networkx as nx
import matplotlib.pyplot as plt
from users import get_user_pairs_from_csv, init_users, parse_user_seller_csv
import sellers

class FashionGraph:
    def __init__(self, directed=False):
        if directed:
            self.graph = nx.DiGraph()
        else:
            self.graph = nx.Graph()

    def add_user(self, user_id, reasons=None):
        self.graph.add_node(user_id, type="user")

    def add_seller(self, seller_id, reasons=None):
        self.graph.add_node(seller_id, type="seller")

    def add_edge(self, node1, node2):
        self.graph.add_edge(node1, node2)

    def add_user_seller_edge(self, user_id, seller_id, reason: str):
        self.graph.add_edge(user_id, seller_id, reason=reason)

    def merge_nx_graph(self, other_graph: nx.Graph, default_node_type: str = None):
        """
        Merge nodes/edges from another NetworkX graph into self.graph.
        Preserves node/edge attributes.
        If default_node_type is provided, nodes missing a 'type' get that type.
        """
        # Add nodes (preserve attributes)
        for n, attrs in other_graph.nodes(data=True):
            attrs = dict(attrs)  # copy so we can safely modify
            if default_node_type is not None:
                attrs.setdefault("type", default_node_type)
            self.graph.add_node(n, **attrs)

        # Add edges (preserve attributes)
        for u, v, eattrs in other_graph.edges(data=True):
            self.graph.add_edge(u, v, **dict(eattrs))

def visualize_graph(G):
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(G, seed=42)

    user_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "user"]
    seller_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "seller"]

    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=user_nodes,
        node_color="skyblue",
        node_size=800,
        label="Users"
    )

    if seller_nodes:
        nx.draw_networkx_nodes(
            G,
            pos,
            nodelist=seller_nodes,
            node_color="lightgreen",
            node_size=900,
            node_shape="s",
            label="Sellers"
        )

    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.7)
    nx.draw_networkx_labels(G, pos, font_size=10)

    plt.legend()
    plt.title("Fashion Network Graph")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("fashion_graph.png")
    plt.close()

if __name__ == "__main__":
    G = FashionGraph(directed=False)
    # Get sellers graph (assumed NetworkX Graph)
    G_sellers = sellers.get_seller_graph()
    # Merge sellers graph into the unified FashionGraph.
    # Force seller nodes to have type="seller" if they don't already.
    G.merge_nx_graph(G_sellers, default_node_type="seller")
    init_users("friends.csv", G)
    visualize_graph(G.graph)

    edge_list = parse_user_seller_csv("user_seller_edges.csv")

    print("User-Seller Edges: ", edge_list[0])

    for user_id, seller_id, reason in edge_list:
        print(f"Adding edge: User {user_id} -> Seller {seller_id} (Reason: {reason})")
        G.add_user_seller_edge(user_id, seller_id, reason)
        break