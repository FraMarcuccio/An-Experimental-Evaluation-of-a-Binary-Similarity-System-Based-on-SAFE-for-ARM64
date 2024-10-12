import networkx as nx

class GraphManager:

    def create_undirected_graph(self, result_dict):
        G = nx.Graph()  # Undirected graph
        for node, destinations in result_dict.items():
            for dest in destinations:
                G.add_edge(node, dest)  # Edges
        return G

    # Visit a node and then explore all its neighbors before moving on to the neighbors of its neighbors.
    def bfs(self, graph, start_node):
        if start_node is None or start_node not in graph:
            return []  # or any other default value
        
        visited = set()
        queue = [start_node]  # Queue to maintain nodes to visit
        bfs_result = []

        while queue:
            node = queue.pop(0)
            if node not in visited:
                bfs_result.append(node)
                visited.add(node)
                # Check if the node exists in the graph before retrieving its neighbors
                if node in graph:
                    # Add neighbors of the current node
                    queue.extend(graph.neighbors(node))
                else:
                    print(f"Node {node} not found in the graph.")
        
        return bfs_result

    # Visit a node and then explore all its neighbors before going back and exploring the neighbors' neighbors.
    def dfs(self, graph, start_node):
        if start_node is None or start_node not in graph:
            return []  # or any other default value
        
        visited = set()
        stack = [start_node]  # Stack to maintain nodes to visit
        dfs_result = []

        while stack:
            node = stack.pop()
            if node not in visited:
                dfs_result.append(node)
                visited.add(node)
                # Check if the node exists in the graph before retrieving its neighbors
                if node in graph:
                    # Add neighbors of the current node
                    stack.extend(graph.neighbors(node))
                else:
                    print(f"Node {node} not found in the graph.")

        return dfs_result