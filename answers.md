# DPS970 – Activity 1: Written Answers

| | |
|---|---|
| **Name** | Trung Hieu Duong |
| **Student ID** | 160982237 |
| **Course** | DPS970 – AI for Software Developers |
| **Due date** | October 11, 2026 |

---

## Question 1 – Spam Filter Email Agent

### a) PEAS

| | Description |
|---|---|
| **Performance measure** | Number of emails put in the right folder. Few good emails sent to spam (false positives) and few spam emails left in the inbox (false negatives). The rules are always followed, and every email ends up in exactly one folder. |
| **Environment** | The incoming `.eml` files, the allow list, the restrict list, the bad word list, and the output folders `spam/` and `email/`. |
| **Actuators** | Moving (or copying) each email file into `spam/` or `email/`. |
| **Sensors** | Reading the `.eml` file: the `From:` header, the body and any text attachments (decoded from base64, quoted-printable or HTML). Reading the three list files. |

### b) Properties of the task environment

| Property | Answer | Why |
|---|---|---|
| Observable | **Partially observable** | The agent can read the headers, the body text and text attachments. But some content may be encrypted or unreadable, so the agent may not see everything in an email. |
| Agents | **Single-agent** | Only the filter makes decisions. |
| Deterministic | **Deterministic** | The same email with the same lists always gives the same result. |
| Episodic | **Episodic** | Each email is separate. Sorting one email doesn't affect the next one. |
| Static | **Static** | The email and the lists don't change while the agent decides. |
| Discrete | **Discrete** | A set of separate emails and only two actions (spam or email). |
| Known | **Known** | All the rules are given (the three lists and the "more than 5 bad words" limit). |

### c) Best agent type: Simple reflex agent

A **simple reflex agent** (AIMA Fig. 2.10) picks an action using only the current percept and **condition–action rules**. This fits the problem:

1. **The task is episodic.** The right folder depends only on the current email, so the agent doesn't need memory (a model-based agent isn't needed).
2. **The rules are already if–then rules**, checked in this order:
   - if the sender domain is on the allow list → `email/`
   - else if the sender domain is on the restrict list → `spam/`
   - else if the body has more than 5 bad words → `spam/`
   - else → `email/`

   The allow list is checked first because the assignment says allowed emails are not spam "regardless of its contents."
3. **There is no goal to plan for and nothing to trade off**, so a goal-based or utility-based agent would add complexity for no benefit.
4. **The environment is deterministic, static and known**, so fixed rules always give the correct action.

A simple reflex agent works best in a fully observable environment. Ours is only partially observable, but the rules only use what the agent can see (the sender domain and the readable text), so it still works. One limitation is that the agent can't learn new spam words. A **learning agent** would be the next step.

### d) Implementation

- `spam_agent/agent_q1.py`: the simple reflex agent
- `spam_agent/environment_q1.py`: the environment (reads emails, moves files)

| Book (Fig. 2.10) | Our code |
|---|---|
| `persistent: rules` | `self.rules`, a list of `Rule(condition, action)` |
| `state ← INTERPRET-INPUT(percept)` | `interpret_input(percept)` returns the sender domain, allow/restrict list status and bad word count |
| `rule ← RULE-MATCH(state, rules)` | `rule_match(state, rules)` returns the first matching rule |
| `action ← rule.ACTION` | `rule.action`, either `MOVE_TO_SPAM` or `MOVE_TO_EMAIL` |

Output of `python -m spam_agent.environment_q1 tests/emails output`:

```
email <- 01_allow_clean.eml           (sender domain is on allow list)
email <- 02_allow_many_bad.eml        (sender domain is on allow list)
spam  <- 03_restrict_clean.eml        (sender domain is on restrict list)
email <- 04_unknown_clean.eml         (default: no spam rule matched)
email <- 05_unknown_5_bad.eml         (default: no spam rule matched)
spam  <- 06_unknown_6_bad.eml         (more than 5 bad words in body)
spam  <- 07_base64_body.eml           (more than 5 bad words in body)
spam  <- 08_text_attachment.eml       (more than 5 bad words in body)
email <- 09_subdomain_allow.eml       (sender domain is on allow list)
spam  <- 10_subdomain_restrict.eml    (sender domain is on restrict list)
spam  <- 11_uppercase_bad.eml         (more than 5 bad words in body)
email <- 12_both_lists.eml            (sender domain is on allow list)
spam  <- 13_lookalike_domain.eml      (more than 5 bad words in body)
spam  <- 14_html_body.eml             (more than 5 bad words in body)
email <- 15_binary_attachment.eml     (default: no spam rule matched)
spam  <- 16_quoted_printable.eml      (more than 5 bad words in body)
spam  <- 17_phrases.eml               (more than 5 bad words in body)
email <- 18_similar_words.eml         (default: no spam rule matched)

18 emails processed: 10 spam, 8 email
```

---

## Question 2 – Three-Jug Search Problem

Three jugs hold 12, 8 and 3 gallons. Using a faucet and the ground, we need to measure exactly 1 gallon.

### a) Problem definition

**State:** a tuple `(a, b, c)` = gallons in the 12-, 8- and 3-gallon jugs, with `0 ≤ a ≤ 12`, `0 ≤ b ≤ 8`, `0 ≤ c ≤ 3`.
- The amounts are always whole numbers, because every action fills, empties, or pours until a jug is full or empty.
- There are at most 13 × 9 × 4 = 468 states, and **314** of them can be reached from the start.

**Initial state:** `(0, 0, 0)`, all jugs empty.

**Goal states:** any state where a jug holds exactly 1 gallon, for example `(1, 8, 3)`.
Goal test: `a == 1 or b == 1 or c == 1`.

**Actions:** 3 fills + 3 empties + 6 pours = 12, so the branching factor is b ≤ 12. Actions that wouldn't change the state are not allowed.

| Action | Meaning | Allowed when |
|---|---|---|
| `Fill(i)` | fill jug *i* from the faucet | jug *i* is not full |
| `Empty(i)` | pour jug *i* onto the ground | jug *i* is not empty |
| `Pour(i, j)` | pour jug *i* into jug *j* | jug *i* is not empty and jug *j* is not full |

**Transition model** `RESULT(s, action)`, with `cap = (12, 8, 3)`:
- `Fill(i)`: `s[i] = cap[i]`
- `Empty(i)`: `s[i] = 0`
- `Pour(i, j)`: `amount = min(s[i], cap[j] − s[j])`, then `s[i] −= amount` and `s[j] += amount`. Pouring stops when jug *i* is empty or jug *j* is full.

**Action cost:** 1 per action, so the path cost is the number of steps.

### b) Does a heuristic make sense?

**Yes, one can be defined, but it doesn't help much here.**

A heuristic h(n) estimates the number of steps left to the goal. For A*, it must never overestimate (be admissible).

"How far each jug is from 1 gallon" is a bad heuristic. One pour can move up to 8 gallons in a single step, so gallons don't match steps, and this guess can be too high (**not admissible**).

An admissible heuristic:
- **h = 0** if a jug already has 1 gallon
- **h = 1** if one action can produce 1 gallon
- **h = 2** otherwise

This never overestimates. A goal needs 0 actions, a state one action away needs exactly 1, and any other state needs at least 2. Our tests confirm this for all 314 reachable states. However, it only separates "goal", "one step away" and "further", so it gives very little guidance. With so few states (every reachable state is at most 5 steps from a goal), plain BFS is enough.

### c) Is any search algorithm guaranteed to reach a goal?

**No.** It depends on the algorithm.

A solution exists: BFS finds one in 3 steps, and since gcd(12, 8, 3) = 1, 1 gallon can be measured. The state space is **finite** but has **cycles**. For example, `Fill 3` then `Empty 3` returns to `(0, 0, 0)`.

| Algorithm | Guaranteed? | Why |
|---|---|---|
| Breadth-first search | **Yes** | Complete when b is finite (b ≤ 12). Also finds the shortest path, since every step costs 1. |
| Uniform-cost search | **Yes** | Behaves like BFS when all step costs are equal. |
| Iterative deepening | **Yes** | Complete, and optimal when every step costs 1. |
| Depth-first graph search (remembers visited states) | **Yes** | The space is finite and no state is repeated, so it must stop. It may not find the shortest path. |
| Depth-first tree search (no repeated-state check) | **No** | Can loop forever, for example `Fill 3 → Empty 3 → Fill 3 → …`. |
| Depth-limited search with limit < 3 | **No** | The goal is 3 steps deep, so it returns *cutoff*. |
| Greedy best-first tree search | **No** | Can loop between states. Only complete in a finite space with repeated-state checking. |

So, only **complete** algorithms are guaranteed to reach the goal: ones that search level by level (BFS, UCS, IDS) or remember visited states. As the lecture slides say: "DFS fails in spaces with loops… modify to avoid repeated states ⇒ complete in finite spaces."

### d) Implementation

- `jugs/problem_q2.py`: `JugProblem`, which holds the initial state, `is_goal`, `actions`, `result` and `action_cost` from part a)
- `jugs/node_q2.py`: `Node` and `expand()` (AIMA Fig. 3.7)
- `jugs/bfs_q2.py`: `breadth_first_search()`, following AIMA Fig. 3.9 line by line. It uses a FIFO `frontier`, a `reached` set so no state is added twice, and a goal test when each child is generated.

Output of `python -m jugs.bfs_q2`:

```
Jugs (12, 8, 3), start (0, 0, 0), target 1 gallon(s)
Step 0: start                    (0, 0, 0)
Step 1: Fill 12-gal              (12, 0, 0)
Step 2: Pour 12-gal -> 8-gal     (4, 8, 0)
Step 3: Pour 12-gal -> 3-gal     (1, 8, 3)

Solved in 3 steps.
```

The 12-gallon jug ends with exactly 1 gallon, which is the goal.
