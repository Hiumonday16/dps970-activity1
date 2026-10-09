# ------------------------------------------------------------------------
# environment_q1.py
# Question 1 (d) - the ENVIRONMENT the spam agent lives in.
#
# The environment:
#   1. reads each .eml file in an inbox folder        (provides PERCEPTS)
#   2. gives the file's contents to the agent          (agent decides)
#   3. performs the agent's action: put the file in
#      <output>/spam/ or <output>/email/               (ACTUATORS)
#
# Run from the project root:
#   python -m spam_agent.environment_q1 tests/emails output
# ------------------------------------------------------------------------

import argparse                    # reads command-line arguments
import shutil                      # copies / moves files
from pathlib import Path

from spam_agent.agent_q1 import SimpleReflexSpamAgent, MOVE_TO_SPAM


def run(inbox, output_dir, agent, move=False):
    # Runs the agent on every .eml file in `inbox`.
    # move=False -> COPY files (keeps the test data intact; default)
    # move=True  -> MOVE files (real mail-filter behaviour)
    # Returns a dict {file name: (action, rule name)} so results can be
    # printed or checked by tests.
    inbox = Path(inbox)
    output_dir = Path(output_dir)

    # Create the two destination folders if they do not exist yet.
    spam_dir = output_dir / "spam"
    email_dir = output_dir / "email"
    spam_dir.mkdir(parents=True, exist_ok=True)
    email_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    # sorted() makes the order predictable (nicer output, stable tests)
    for eml_file in sorted(inbox.glob("*.eml")):
        percept = eml_file.read_bytes()      # PERCEPT: raw contents of the file
        action = agent(percept)              # AGENT PROGRAM chooses an action

        # ACTUATOR: carry out the chosen action on the file system.
        destination = spam_dir if action == MOVE_TO_SPAM else email_dir
        if move:
            shutil.move(str(eml_file), destination / eml_file.name)
        else:
            shutil.copy2(eml_file, destination / eml_file.name)

        results[eml_file.name] = (action, agent.last_rule.name)
    return results


def main():
    # Command-line entry point, so the demo can be run from a terminal.
    parser = argparse.ArgumentParser(description="Simple reflex spam filter agent")
    parser.add_argument("inbox", help="folder containing .eml files")
    parser.add_argument("output", help="folder where spam/ and email/ will be created")
    parser.add_argument("--move", action="store_true", help="move files instead of copying")
    parser.add_argument("--allow", help="path to allow list (default: spam_agent/data/allow_list.txt)")
    parser.add_argument("--restrict", help="path to restrict list")
    parser.add_argument("--bad-words", help="path to bad word list")
    args = parser.parse_args()

    # Build the agent from the list files.
    agent = SimpleReflexSpamAgent.from_files(args.allow, args.restrict, args.bad_words)

    # Run the environment and print a small report.
    results = run(args.inbox, args.output, agent, move=args.move)
    for name, (action, rule) in results.items():
        folder = "spam " if action == MOVE_TO_SPAM else "email"
        print(f"{folder} <- {name:28} ({rule})")
    spam_total = sum(1 for a, _ in results.values() if a == MOVE_TO_SPAM)
    print(f"\n{len(results)} emails processed: {spam_total} spam, {len(results) - spam_total} email")


# Only run main() when this file is executed directly, not when imported.
if __name__ == "__main__":
    main()
