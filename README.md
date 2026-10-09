# DPS970 – Activity 1

**Trung Hieu Duong** · Student ID 160982237

The written answers for Q1 a–d and Q2 a–d are in [answers.md](answers.md).

## Requirements

- Python 3.10 or newer
- pytest (`pip install -r requirements.txt`)

## Project layout

```
spam_agent/                 # Question 1
  agent_q1.py               #   simple reflex agent (AIMA Fig 2.10)
  environment_q1.py         #   reads .eml files, carries out the agent's actions
  data/                     #   allow list, restrict list, bad word list
jugs/                       # Question 2
  problem_q2.py             #   JugProblem: initial, is_goal, actions, result, action_cost
  node_q2.py                #   Node + expand (AIMA Fig 3.7)
  bfs_q2.py                 #   breadth_first_search (AIMA Fig 3.9)
tests/
  emails/                   # Q1 test data: 18 .eml files covering each rule and edge case
  jug_cases_q2.json         # Q2 test data: 8 jug problems with the expected number of steps
  test_spam_agent_q1.py     # Q1 tests
  test_jugs_q2.py           # Q2 tests
.github/workflows/tests.yml # runs all tests automatically on GitHub
```

## Running the tests

From the project root folder (the folder containing this README):

```
pip install -r requirements.txt
pytest -v
```

This should show **56 passed** (28 for Q1, 28 for Q2).

The same tests run automatically on GitHub Actions (`.github/workflows/tests.yml`) on every push and pull request.

## Running Question 1: spam filter

```
python -m spam_agent.environment_q1 tests/emails output
```

This copies every email in `tests/emails/` into `output/spam/` or `output/email/` and prints which rule decided each one. Options:

- `--move`: move the files instead of copying them
- `--allow FILE`, `--restrict FILE`, `--bad-words FILE`: use different list files

## Running Question 2: three-jug BFS

```
python -m jugs.bfs_q2
```

This solves the 12/8/3-gallon problem (measure 1 gallon) and prints each step. You can also try other problems:

```
python -m jugs.bfs_q2 --caps 4 3 --target 2
python -m jugs.bfs_q2 --caps 8 5 3 --start 8 0 0 --target 4
python -m jugs.bfs_q2 --caps 4 6 --target 1        # no solution
```

## Assumptions

### Question 1
1. **Rule priority:** allow list > restrict list > bad-word rule > default (not spam). If a domain is on both lists, the allow list wins, because the spec says allow-listed mail is non-spam "regardless of its contents."
2. **Restrict list:** the assignment calls these "safe domains," but since the mail is classified as spam, they are treated as *unsafe* domains.
3. **Threshold:** spam means **more than 5** bad words, so 5 is not spam and 6 is spam.
4. **Counting:** every occurrence counts ("free free" = 2). Matching ignores case and uses whole words only ("freedom" does not match "free"). Entries with spaces ("act now") are matched as phrases.
5. **Domains:** the sender is taken from the `From:` header. Subdomains match (`mail.myseneca.ca` matches `myseneca.ca`), but lookalikes do not (`notgithub.com` does not match `github.com`).
6. **Body:** all `text/*` parts are read, including text attachments, after decoding base64, quoted-printable and charsets. HTML tags are removed. Non-text parts and parts that can't be decoded are ignored.

### Question 2
1. **Goal:** "measure out exactly one gallon" means any one jug holds exactly 1 gallon.
2. **Actions:** an action that changes nothing (filling a full jug, emptying an empty jug, pouring into a full jug) is not generated.
3. **Cost:** every action costs 1, so BFS returns the solution with the fewest steps.
