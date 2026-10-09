# ------------------------------------------------------------------------
# node_q2.py
# Search tree NODE and the EXPAND function (AIMA 4th ed., Figure 3.7).
#
# A STATE is just a jug configuration like (4, 8, 0).
# A NODE is a data structure in the search tree. It stores:
#   state     - the state this node represents
#   parent    - the node that generated this node
#   action    - the action applied to the parent to get here
#   path_cost - total cost from the initial state (g(n))
# ------------------------------------------------------------------------

import math


class Node:
    def __init__(self, state, parent=None, action=None, path_cost=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.path_cost = path_cost

    def __repr__(self):
        return f"<Node {self.state}>"

    def __len__(self):
        # Depth of the node = number of actions from the root.
        return 0 if self.parent is None else 1 + len(self.parent)


# Special node returned when no solution exists (same idea as the
# book's code: failure has an infinite path cost).
failure = Node("failure", path_cost=math.inf)


def expand(problem, node):
    # EXPAND(problem, node) from Figure 3.7:
    #   s <- node.STATE
    #   for each action in problem.ACTIONS(s) do
    #     s' <- problem.RESULT(s, action)
    #     cost <- node.PATH-COST + problem.ACTION-COST(s, action, s')
    #     yield NODE(STATE=s', PARENT=node, ACTION=action, PATH-COST=cost)
    s = node.state
    for action in problem.actions(s):
        s1 = problem.result(s, action)
        cost = node.path_cost + problem.action_cost(s, action, s1)
        yield Node(s1, node, action, cost)


def path_actions(node):
    # Walks back through the parents to get the list of actions
    # from the initial state to this node (the SOLUTION).
    if node.parent is None:
        return []
    return path_actions(node.parent) + [node.action]


def path_states(node):
    # Same as path_actions, but returns the list of states.
    if node in (failure, None):
        return []
    return path_states(node.parent) + [node.state]
