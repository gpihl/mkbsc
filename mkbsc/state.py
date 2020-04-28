import networkx as nx
import hashlib
from networkx.drawing.nx_pydot          import to_pydot
from subprocess import call

class State:
    """Represents a game state, with separate knowledge for each player

    The knowledge is stored as a tuple, and can be accessed by State().knowledges[playerindex]
    or simply State()[playerindex]. The players are zero-indexed. In the base game, the states'
    knowledge should be an integer or short string, the same for all players. This case is
    treated separately and the tuple State().knowledges is a singleton. When applying the KBSC, the new
    states' knowledge are sets of states from the previous iteration. For example, after two
    iterations the states' knowledge are sets of states, whose knowledge are sets of states,
    whose knowledge could be integers."""
    
    def __init__(self, *knowledges):
        """Create a new state

        ex. s = State(1)"""
        
        self.knowledges = tuple(knowledges)
        
    def __getitem__(self, index):
        """Get the knowledge of the specified player

        Will work as expected even if knowledges is a singleton"""
        
        if len(self.knowledges) == 1:
            return self.knowledges[0]
        else:
            return self.knowledges[index]
            
    def __str__(self):
        return repr(self)
        
    compact_representation = False
    def __repr__(self):
        """Return a compact string representation of the knowledge"""

        #if we are writing to a dot file we only need a unique string, not the full representation
        if State.compact_representation:
            return str(id(self))
        
#        return "s" + str(self.knowledges)
        if len(self.knowledges) == 1:
            if type(self.knowledges[0]) is frozenset:
                return str(set(self.knowledges[0]))
            else:
                return str(self.knowledges[0])
        else:
            return str(tuple(set(self.knowledges[i]) for i in range(len(self.knowledges))))
    
    __indent = "\t"
    def epistemic_verbose(self, level=0):
        """Return a verbose representation of the knowledge. Not recommended for overly iterated games."""
        if len(self.knowledges) == 1:
            return State.__indent * level + "We are in " + str(self.knowledges[0]) + "\n"
        
        s = ""
        for player, knowledge in enumerate(self.knowledges):
            s += State.__indent * level + "Player " + str(player) + " knows:\n"
            s += (State.__indent * (level + 1) + "or\n").join([state.epistemic(level + 1) for state in knowledge])

        return s

    def _node_str(self, G, node):
        return "(" + str(G.nodes[node]['player']) + ", " + G.nodes[node]['label'] + ")\t" + node[:5]

    def _edge_str(self, G, edge):
        return self._node_str(G, edge[0]) + "\t" + self._node_str(G, edge[1]) # + "\t\t" + edge[0][:5] + "\t" + edge[1][:5]

    def _epistemic_subtree_equals(self, G, node1, node2):
        # print("\t\tComparing subtrees starting from:")
        # print("\t\t\t" + node1[:5])
        # print("\t\t\t" + node2[:5])

        queue1 = [node1]
        queue2 = [node2]

        while len(queue1) != 0 and len(queue2) != 0:
            curr1 = queue1[0]
            curr2 = queue2[0]

            if (G.nodes[curr1]['label'] != G.nodes[curr2]['label']) or (G.nodes[curr1]['player'] != G.nodes[curr2]['player']):
                # print("\t\tThese nodes did not match:")
                # print("\t\t\t" + self._node_str(G, curr1))
                # print("\t\t\t" + self._node_str(G, curr2))
                return False

            queue1 = queue1[1:]
            queue2 = queue2[1:]
            neighbors1 = list(G.neighbors(curr1))
            neighbors2 = list(G.neighbors(curr2))

            if len(neighbors1) == 0 or len(neighbors2) == 0:
                # print("\t\tTrees match!")
                return True

            if len(neighbors1) != len(neighbors2):
                # print("\t\tDifferent number of children")
                return False

            for i in range(len(neighbors1)):
                n1 = neighbors1[i]
                n2 = neighbors2[i]
                queue1.append(n1)
                queue2.append(n2)

        # print("\t\tTrees match!")
        return True

    def _epistemic_nodes_at_depth(self, G, depth):
        root = list(G.edges)[0][0]
        current_depth = [root]
        next_depth = []
        while depth != 0:
            for n in current_depth:
                for m in G.neighbors(n):
                    next_depth.append(m)

            current_depth = next_depth
            next_depth = []
            depth -= 1

        return current_depth

    def _get_epistemic_depth(self, G, node):
        depth = 0
        nodes_at_depth = set(self._epistemic_nodes_at_depth(G, depth))
        while len(nodes_at_depth) > 0:
            if node in nodes_at_depth:
                return depth
            depth +=1
            nodes_at_depth = set(self._epistemic_nodes_at_depth(G, depth))


    def _has_recursive_ancestor(self, G, node):
        # print("\tChecking to see if leaf has recursive ancestor: " + self._node_str(G, node))
        depth = 0
        node_depth = self._get_epistemic_depth(G, node)

        while depth < node_depth:
            nodes = self._epistemic_nodes_at_depth(G, depth)
            for n in nodes:
                if self._epistemic_subtree_equals(G, node, n):
                    return True
            depth += 1

        return False

    def epistemic_trees_recursive_at_depth(self, depth):
        player = 0
        res = True
        for state in self.knowledges:
            # print("CHECKING IF TREE IS RECURSIVE AT DEPTH: " + str(depth))
            # The e-tree
            G = nx.DiGraph()

            # Add the nodes recursively 
            self.parse_knowledge(None, player, G)
            nodes_at_depth = self._epistemic_nodes_at_depth(G, depth)
            for node in nodes_at_depth:
                curr_res = self._has_recursive_ancestor(G, node)
                res = res and curr_res
                if not res:
                    print(self.epistemic_tree())
                    return res

            player += 1

        return res

    def epistemic_tree(self, file = "png"):
        """This function creates an e-tree for a specific player based on the knowledge gained from the
        MKBSC-algorithm. """

        # Build one tree for every player
        player = 0
        call_string = []

        for state in self.knowledges:
            # The e-tree
            G = nx.Graph()

            # Add the nodes recursively 
            self.parse_knowledge(None, player, G)

            # Create a file
            arr = to_pydot(G).to_string()
            with open("pictures/temp/" + str(player) + ".dot", "w") as dotfile:
                dotfile.write(arr)


            call(["dot", "-T" + file, "-Gdpi=160", "pictures/temp/" + str(player) + ".dot", "-o", "pictures/temp/" + str(player) + "." + file])


            call_string.append("pictures/temp/" + str(player) + "." + file)
            player += 1
        
        # Combine images
        image_name = "pictures/temp/" + str(id(self)) + "." + file
        call(["convert", "+append"] + call_string + [image_name])
        return image_name


    def parse_knowledge(self, parent, player, G):
        '''Function for recursively building the e-tree'''

        def create_id(node, parent, player):
            '''This function generates a uniqe id for a node in the e-tree.
               The same node in the tree will always get the same id'''
            
            # The node id ends with the label of the node
            hash_string = node + str(player)

            # Iterate until the root node has been found
            # and for every node passed on the way, the
            # label is added at the beginning of the hash string
            while not parent == None:
                hash_string = str(G.nodes[parent]["label"]) + str(G.nodes[parent]["player"]) + hash_string
                parent = G.nodes[parent]["parent"]
            
            # Hash the string
            node_id = hashlib.sha1(str.encode(hash_string)).hexdigest()
            return node_id
        

        # Allows for indexing of state knowledges
        indexed_knowledges = tuple(self.knowledges[player])


        # Base case when a tree node for the e-tree is found
        if len(indexed_knowledges[0].knowledges) == 1:

            # Create the label for the node, give it a unique ID and add it to the graph
            # If the node is already in the graph nothing will happen
            tree_node = "{" + ", ".join([str(state.knowledges[0]) for state in indexed_knowledges]) + "}"
            node_id = create_id(tree_node, parent, player)
            G.add_node(node_id, label=tree_node, parent=parent, player=player)
            
            # Return the node ID so it can be used to add edges and child nodes
            return node_id
            
        else:
            # Add parent node
            parent_node = indexed_knowledges[0].parse_knowledge(parent, player, G)

            # Add child nodes to parent node
            for state in indexed_knowledges:
                for p in range(len(state.knowledges)):

                    # Check state for all players except for the current player
                    if p == player:
                        continue
                    
                    # Add child nodes and edges to the parent node
                    child_node = state.parse_knowledge(parent_node, p, G)
                    G.add_edge(parent_node, child_node, label=p)

            # Return the parent node        
            return parent_node

    def epistemic_nice(self, level=0):
        """Return a compact but still quite readable representation of the knowledge"""
        def __wrap(state, l):
            if len(state.knowledges) > 1:
                #print("Wrap")
                return "(" + state.epistemic_nice(l + 1) + ")"
            else:
                #print("Wrap : " + str(state.knowledges[0]))
                return str(state.knowledges[0])
        # Outer level of player knowledge
        if level == 0:
            if len(self.knowledges) > 1:
                # More than one epistemic level
                #print("Level = 0 : len > 1")
                return "\n".join(["{" + ", ".join([state.epistemic_nice(level + 1) for state in knowledge]) + "}" for knowledge in self.knowledges])
            else:
                # One epistemic level
                if type(self.knowledges[0]) is frozenset:
                    # ??
                    #print("Level = 0 : len <= 1 : is frozenset")
                    return "{" + ", ".join([state.epistemic_nice(level + 1) for state in self.knowledges[0]]) + "}"
                else:
                    # Only used when one epistemic level
                    #print("Level = 0 : len <= 1 : not frozenset")
                    #print("Level = 0 : " + str(self.knowledges[0]))
                    return str(self.knowledges[0])
        # Inner level
        else:
            if len(self.knowledges) > 1:
                # Used when more than two epistemic levels in total
                #print("Level > 0  : len > 1")
                return "-".join(["".join([__wrap(state, level) for state in knowledge]) for knowledge in self.knowledges])
            else:
                if type(self.knowledges[0]) is frozenset:
                    # ??
                    #print("Level > 0 : len <= 1 : is frozenset")
                    return "{" + ", ".join([state.epistemic_nice(level + 1) for state in self.knowledges[0]]) + "}"
                else:
                    # Only used when two epistemic levels
                    #print("Level > 0 : len <= 1 : not frozenset")
                    #print("Level > 0 : " + str(self.knowledges[0]))
                    return str(self.knowledges[0])
                
    def epistemic_isocheck(self):
        """Return the most compact representation, only containing which states in the base game are possible in this state"""
        return ", ".join([str(state.knowledges[0]) for state in self.consistent_base()])

    def consistent_base(self):
        """Return the states in the base game that are possible in this state

        This assumes that the knowledges in the base game are singletons"""
        def _pick(_set):
            for x in _set:
                return x
            raise None
        
        states = [self]
        if len(self.knowledges) == 1 and type(self.knowledges[0]) is frozenset:
            states = {self.knowledges[0]}
        
        while len(_pick(states).knowledges) > 1:
            states = set.intersection(*[set.intersection(*[set(state[player]) for player in range(len(self.knowledges))]) for state in states])
        
        return states


    def epistemic_depth(self, ):
        """Returns the depth of the graph"""
        depth = 1
        indexed_knowledges = tuple(self.knowledges[0])

        while(len(indexed_knowledges[0].knowledges)) != 1:
            indexed_knowledges = tuple(indexed_knowledges[0].knowledges[0])
            depth += 1

        return depth
        

    #workaround to make sure the networkx isomorphism check works
    orderable = False
    def __gt__(self, other):
        assert State.orderable
        return id(self) > id(other)
    def __lt__(self, other):
        assert State.orderable
        return id(self) < id(other)
