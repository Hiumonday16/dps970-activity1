# ------------------------------------------------------------------------
# bfs_q2.py
# Question 2 (d) - Breadth-first search, AIMA 4th ed., Figure 3.9:
#
#   function BREADTH-FIRST-SEARCH(problem) returns a solution node or failure
#     node <- NODE(problem.INITIAL)
#     if problem.IS-GOAL(node.STATE) then return node
#     frontier <- a FIFO queue, with node as an element
#     reached <- {problem.INITIAL}
#     while not IS-EMPTY(frontier) do
#       node <- POP(frontier)
#       for each child in EXPAND(problem, node) do
#         s <- child.STATE
#         if problem.IS-GOAL(s) then return child
#         if s is not in reached then
#           add s to reached
#           add child to frontier
#     return failure
#
# Run from the project root:
#   python -m jugs.bfs_q2                       (default 12/8/3 jugs, target 1)
#   python -m jugs.bfs_q2 --caps 8 5 3 --start 8 0 0 --target 4
# ------------------------------------------------------------------------

import argparse
from collections import deque      # deque = fast FIFO queue

from jugs.node_q2 import Node, expand, failure, path_actions, path_states
from jugs.problem_q2 import JugProblem


def breadth_first_search(problem):
    # node <- NODE(problem.INITIAL)
    node = Node(problem.initial)

    # if problem.IS-GOAL(node.STATE) then return node
    if problem.is_goal(node.state):
        return node

    # frontier <- a FIFO queue, with node as an element
    frontier = deque([node])

    # reached <- {problem.INITIAL}
    # (a set of states we have already generated, so no state is added twice)
    reached = {problem.initial}

    # while not IS-EMPTY(frontier) do
    while frontier:
        # node <- POP(frontier)   -> take the OLDEST node (first in, first out)
        node = frontier.popleft()

        # for each child in EXPAND(problem, node) do
        for child in expand(problem, node):
            s = child.state

            # EARLY goal test: check the child as soon as it is generated
            if problem.is_goal(s):
                return child

            # only add states we have never seen before
            if s not in reached:
                reached.add(s)
                frontier.append(child)   # new nodes go to the END of the queue

    # frontier is empty and no goal was found
    return failure


def main():
    # Command-line demo: solves the problem and prints every step.
    parser = argparse.ArgumentParser(description="Three-jug problem solved with BFS")
    parser.add_argument("--caps", type=int, nargs="+", default=[12, 8, 3], help="jug capacities")
    parser.add_argument("--start", type=int, nargs="+", help="initial amounts (default: all empty)")
    parser.add_argument("--target", type=int, default=1, help="amount to measure (default 1)")
    args = parser.parse_args()

    problem = JugProblem(args.caps, args.start, args.target)
    goal = breadth_first_search(problem)

    if goal is failure:
        print(f"No solution: cannot measure {args.target} gallon(s) with jugs {tuple(args.caps)}")
        return

    # Print the solution path step by step.
    states = path_states(goal)
    actions = path_actions(goal)
    print(f"Jugs {problem.capacities}, start {problem.initial}, target {problem.goal} gallon(s)")
    print(f"Step 0: {'start':24} {states[0]}")
    for step, (action, state) in enumerate(zip(actions, states[1:]), start=1):
        print(f"Step {step}: {problem.describe(action):24} {state}")
    print(f"\nSolved in {goal.path_cost} steps.")


if __name__ == "__main__":
    main()
