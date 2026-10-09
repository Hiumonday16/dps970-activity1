# ------------------------------------------------------------------------
# problem_q2.py
# Question 2 (a) - formal definition of the Three-Jug search problem.
#
# A search problem in AIMA (4th ed., Section 3.1.1) has five parts:
#   1. INITIAL state
#   2. IS-GOAL(state)            -> goal test
#   3. ACTIONS(state)            -> actions that can be done in a state
#   4. RESULT(state, action)     -> transition model
#   5. ACTION-COST(s, a, s')     -> cost of one step
#
# This class follows that structure (the same shape as the Problem class
# in the book's code, aima-python search.py).
# ------------------------------------------------------------------------


class Problem:
    # General search problem (the abstract class from the book).
    # Subclasses override actions, result and is_goal.
    def __init__(self, initial=None, goal=None):
        self.initial = initial
        self.goal = goal

    def actions(self, state):
        raise NotImplementedError

    def result(self, state, action):
        raise NotImplementedError

    def is_goal(self, state):
        return state == self.goal

    def action_cost(self, s, action, s1):
        return 1                      # default: every step costs 1

    def h(self, node):
        return 0                      # default heuristic: no information


class JugProblem(Problem):
    # The three-jug problem.
    #
    # STATE:   a tuple (a, b, c) = gallons currently in each jug.
    #          With capacities (12, 8, 3): 0<=a<=12, 0<=b<=8, 0<=c<=3.
    # INITIAL: (0, 0, 0)  -> all jugs empty
    # GOAL:    any jug holds exactly `target` gallons (1 by default)
    # ACTIONS: ("Fill", i)     fill jug i from the faucet
    #          ("Empty", i)    pour jug i out onto the ground
    #          ("Pour", i, j)  pour jug i into jug j until i is empty or j is full

    def __init__(self, capacities=(12, 8, 3), initial=None, target=1):
        self.capacities = tuple(capacities)
        # If no initial state is given, start with every jug empty.
        if initial is None:
            initial = tuple(0 for _ in self.capacities)
        super().__init__(initial=tuple(initial), goal=target)

    # ---- GOAL TEST -------------------------------------------------------
    def is_goal(self, state):
        # Goal reached when at least one jug holds exactly the target amount.
        return self.goal in state

    # ---- ACTIONS(s) ------------------------------------------------------
    def actions(self, state):
        # Returns only the actions that change the state.
        # (Filling a full jug or emptying an empty jug does nothing,
        #  so those actions are left out.)
        acts = []
        n = len(self.capacities)
        for i in range(n):
            if state[i] < self.capacities[i]:      # jug i is not full
                acts.append(("Fill", i))
            if state[i] > 0:                       # jug i is not empty
                acts.append(("Empty", i))
            for j in range(n):
                # can pour i -> j if i has water and j has free space
                if i != j and state[i] > 0 and state[j] < self.capacities[j]:
                    acts.append(("Pour", i, j))
        return acts

    # ---- TRANSITION MODEL: RESULT(s, a) ----------------------------------
    def result(self, state, action):
        s = list(state)                            # copy so the old state is not changed
        kind = action[0]
        if kind == "Fill":
            i = action[1]
            s[i] = self.capacities[i]              # jug i becomes full
        elif kind == "Empty":
            i = action[1]
            s[i] = 0                               # jug i becomes empty
        elif kind == "Pour":
            i, j = action[1], action[2]
            # amount poured = whatever is smaller:
            #   what jug i has, or the free space left in jug j
            amount = min(s[i], self.capacities[j] - s[j])
            s[i] -= amount
            s[j] += amount
        else:
            raise ValueError(f"unknown action {action}")
        return tuple(s)                            # tuples can be stored in a set

    # ---- ACTION-COST(s, a, s') -------------------------------------------
    def action_cost(self, s, action, s1):
        return 1                                   # every action counts as one step

    # ---- HEURISTIC (Question 2 b) ----------------------------------------
    def h(self, node):
        # Informal heuristic from the written answer, used only to check
        # the answer in the tests (BFS itself does not use it).
        #   0 -> the state is already a goal
        #   1 -> one action can reach a goal
        #   2 -> otherwise (at least two more actions are needed)
        # It never overestimates the real number of steps (admissible).
        state = node.state if hasattr(node, "state") else node
        if self.is_goal(state):
            return 0
        if any(self.is_goal(self.result(state, a)) for a in self.actions(state)):
            return 1
        return 2

    # ---- Helper for printing ---------------------------------------------
    def describe(self, action):
        # Turns ("Pour", 0, 2) into "Pour 12-gal -> 3-gal" for nicer output.
        cap = self.capacities
        if action[0] == "Pour":
            return f"Pour {cap[action[1]]}-gal -> {cap[action[2]]}-gal"
        return f"{action[0]} {cap[action[1]]}-gal"
