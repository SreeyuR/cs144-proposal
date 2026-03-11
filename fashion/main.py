import networkx as nx
import matplotlib.pyplot as plt
from users import init_users, init_user_seller_edges
import sellers
import numpy as np

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
        for n, attrs in other_graph.nodes(data=True):
            attrs = dict(attrs)
            if default_node_type is not None:
                attrs.setdefault("type", default_node_type)
            self.graph.add_node(n, **attrs)

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

def visualize_soft_bipartite(fashion_graph):
    G = fashion_graph.graph
    plt.figure(figsize=(10, 7))

    users = [n for n, d in G.nodes(data=True) if d.get("type") == "user"]
    sellers = [n for n, d in G.nodes(data=True) if d.get("type") == "seller"]

    pos = nx.spring_layout(G, seed=42, k=0.6)

    for node in users:
        pos[node][0] -= 1.5  

    for node in sellers:
        pos[node][0] += 1.5   

    nx.draw_networkx_nodes(G, pos,
                           nodelist=users,
                           node_color="skyblue",
                           node_size=800,
                           label="Users")

    nx.draw_networkx_nodes(G, pos,
                           nodelist=sellers,
                           node_color="lightgreen",
                           node_shape="s",
                           node_size=900,
                           label="Sellers")

    nx.draw_networkx_edges(G, pos, alpha=0.5)
    nx.draw_networkx_labels(G, pos, font_size=9)

    edge_labels = {
        (u, v): data.get("reason", "")
        for u, v, data in G.edges(data=True)
    }

    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_labels,
        font_size=6,        
        font_color="gray",
        label_pos=0.5,   
        rotate=False,
        bbox=dict(
            boxstyle="round,pad=0.1",
            fc="white",
            ec="none",
            alpha=0.6
        )
    )

    plt.title("Soft Bipartite Layout")
    plt.legend()
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("soft_bipartite_fashion_network.png")
    plt.close()

if __name__ == "__main__":
    G = FashionGraph(directed=False)
    G_sellers = sellers.get_seller_graph()
    # Merge sellers graph into the unified FashionGraph.
    # Force seller nodes to have type="seller" if they don't already.
    G.merge_nx_graph(G_sellers, default_node_type="seller")
    init_users("friends.csv", G)

    init_user_seller_edges(G)

    visualize_graph(G.graph)

    visualize_soft_bipartite(G)