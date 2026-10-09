# ------------------------------------------------------------------------
# test_jugs_q2.py
# Automated tests for Question 2 (three-jug problem + BFS).
# Run from the project root with:   pytest -v
# ------------------------------------------------------------------------

import json
from pathlib import Path

import pytest

from jugs.bfs_q2 import breadth_first_search
from jugs.node_q2 import Node, expand, failure, path_actions, path_states
from jugs.problem_q2 import JugProblem

# Test data: problem instances with the expected number of steps.
CASES = json.loads((Path(__file__).parent / "jug_cases_q2.json").read_text())


@pytest.fixture
def problem():
    # The problem from the assignment: jugs 12, 8, 3 and target 1 gallon.
    return JugProblem()


def all_distances(problem):
    # Helper used only by the tests: finds EVERY reachable state and the
    # real minimum number of steps to reach a goal from each one.
    # It works backwards from the true answer so we can check BFS and the
    # heuristic against it. (Written separately from bfs_q2.py on purpose.)
    states, todo = {problem.initial}, [problem.initial]
    while todo:                                    # 1) collect all reachable states
        s = todo.pop()
        for a in problem.actions(s):
            t = problem.result(s, a)
            if t not in states:
                states.add(t)
                todo.append(t)
    dist = {s: 0 for s in states if problem.is_goal(s)}
    changed = True
    while changed:                                 # 2) relax until nothing changes
        changed = False
        for s in states:
            for a in problem.actions(s):
                t = problem.result(s, a)
                if t in dist and dist.get(s, float("inf")) > dist[t] + 1:
                    dist[s] = dist[t] + 1
                    changed = True
    return states, dist


# ==================== 1. Problem definition (Q2 a) ======================

def test_initial_state(problem):
    assert problem.initial == (0, 0, 0)
    assert not problem.is_goal(problem.initial)


def test_goal_test(problem):
    assert problem.is_goal((1, 8, 3))
    assert problem.is_goal((0, 1, 0))
    assert problem.is_goal((0, 0, 1))
    assert not problem.is_goal((4, 8, 0))


def test_fill_and_empty(problem):
    assert problem.result((0, 0, 0), ("Fill", 0)) == (12, 0, 0)
    assert problem.result((0, 0, 0), ("Fill", 2)) == (0, 0, 3)
    assert problem.result((12, 8, 3), ("Empty", 1)) == (12, 0, 3)


def test_pour_until_target_full(problem):
    # 12 -> 8 when the 12 is full: only 8 fits, 4 stays behind
    assert problem.result((12, 0, 0), ("Pour", 0, 1)) == (4, 8, 0)
    # 12 -> 3 with 4 gallons: only 3 fits, 1 stays behind (the goal!)
    assert problem.result((4, 8, 0), ("Pour", 0, 2)) == (1, 8, 3)


def test_pour_until_source_empty(problem):
    # 3 -> 12: all 3 gallons fit
    assert problem.result((0, 0, 3), ("Pour", 2, 0)) == (3, 0, 0)


def test_water_is_never_created_by_pouring(problem):
    # Pouring only moves water, so the total stays the same.
    s = (7, 5, 2)
    for a in problem.actions(s):
        if a[0] == "Pour":
            assert sum(problem.result(s, a)) == sum(s)


def test_actions_skip_useless_moves(problem):
    acts = problem.actions((12, 0, 0))
    assert ("Fill", 0) not in acts          # already full
    assert ("Empty", 1) not in acts         # already empty
    assert ("Pour", 1, 0) not in acts       # jug 8 is empty
    assert ("Pour", 0, 1) in acts


def test_twelve_actions_at_most(problem):
    # 3 fills + 3 empties + 6 pours = 12 possible actions (the branching factor b)
    for s in [(0, 0, 0), (5, 4, 1), (12, 8, 3)]:
        assert len(problem.actions(s)) <= 12
    assert len(problem.actions((5, 4, 1))) == 12   # every jug is partly full


def test_every_result_stays_inside_the_jugs(problem):
    states, _ = all_distances(problem)
    for s in states:
        for amount, cap in zip(s, problem.capacities):
            assert 0 <= amount <= cap


# ==================== 2. Node / EXPAND ==================================

def test_expand_sets_parent_action_and_cost(problem):
    root = Node(problem.initial)
    children = list(expand(problem, root))
    assert {c.state for c in children} == {(12, 0, 0), (0, 8, 0), (0, 0, 3)}
    for c in children:
        assert c.parent is root
        assert c.path_cost == 1
        assert len(c) == 1                  # depth 1


# ==================== 3. BFS (Q2 d) =====================================

def test_bfs_solves_assignment_problem(problem):
    goal = breadth_first_search(problem)
    assert goal is not failure
    assert problem.is_goal(goal.state)
    assert goal.path_cost == 3
    assert path_actions(goal) == [("Fill", 0), ("Pour", 0, 1), ("Pour", 0, 2)]
    assert path_states(goal) == [(0, 0, 0), (12, 0, 0), (4, 8, 0), (1, 8, 3)]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_bfs_on_test_data(case):
    problem = JugProblem(case["caps"], case["start"], case["target"])
    goal = breadth_first_search(problem)
    if case["steps"] is None:
        assert goal is failure                       # no solution exists
    else:
        assert goal is not failure
        assert goal.path_cost == case["steps"]       # shortest number of steps
        # replay the actions from the start: we must end in the goal state
        s = problem.initial
        for a in path_actions(goal):
            assert a in problem.actions(s)           # each action is legal
            s = problem.result(s, a)
        assert s == goal.state and problem.is_goal(s)


@pytest.mark.parametrize("case", [c for c in CASES if c["steps"] is not None],
                         ids=[c["name"] for c in CASES if c["steps"] is not None])
def test_bfs_is_optimal(case):
    # BFS answer must equal the true shortest distance found by brute force.
    problem = JugProblem(case["caps"], case["start"], case["target"])
    _, dist = all_distances(problem)
    assert breadth_first_search(problem).path_cost == dist[problem.initial]


# ==================== 4. Facts used in the written answers ==============

def test_state_space_is_small_and_finite(problem):
    # Q2 b/c: the space is finite and small (well under 13*9*4 = 468).
    states, dist = all_distances(problem)
    assert len(states) <= 13 * 9 * 4
    assert problem.initial in dist           # a goal is reachable from the start


def test_state_space_has_cycles(problem):
    # Q2 c: Fill then Empty brings us back to the same state, so a search
    # that does not remember visited states can loop forever.
    s = problem.result(problem.initial, ("Fill", 2))
    assert problem.result(s, ("Empty", 2)) == problem.initial


def test_heuristic_is_admissible(problem):
    # Q2 b: h never overestimates the real number of steps left.
    states, dist = all_distances(problem)
    for s in states:
        assert problem.h(s) <= dist[s]
    assert problem.h((1, 0, 0)) == 0
    assert problem.h((4, 8, 0)) == 1
