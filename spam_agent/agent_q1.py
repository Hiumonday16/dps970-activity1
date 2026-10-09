# ------------------------------------------------------------------------
# agent_q1.py
# Question 1 (d) - Spam Filter Email Agent
#
# This file contains the AGENT PROGRAM. It is a SIMPLE REFLEX AGENT that
# follows the structure of AIMA (Russell & Norvig) Figure 2.10:
#
#   function SIMPLE-REFLEX-AGENT(percept) returns an action
#     persistent: rules, a set of condition-action rules
#     state  <- INTERPRET-INPUT(percept)
#     rule   <- RULE-MATCH(state, rules)
#     action <- rule.ACTION
#     return action
#
# The agent never touches the file system itself. It only receives a
# percept (the raw bytes of one .eml file) and returns an action
# ("MOVE_TO_SPAM" or "MOVE_TO_EMAIL"). The environment (environment_q1.py)
# is responsible for actually moving the file (the actuator).
# ------------------------------------------------------------------------

import email                      # Python's built-in library for parsing .eml files
import re                         # regular expressions, used to split text into words
from email import policy          # "policy.default" gives us the modern email API
from email.utils import parseaddr # pulls "user@domain" out of "Name <user@domain>"
from pathlib import Path          # convenient, OS-independent file paths


# ---- The two possible actions the agent can choose ----------------------
MOVE_TO_SPAM = "MOVE_TO_SPAM"     # actuator command: put the email in spam/
MOVE_TO_EMAIL = "MOVE_TO_EMAIL"   # actuator command: put the email in email/


# ---- Folder holding the default list files -------------------------------
DATA_DIR = Path(__file__).parent / "data"


def load_list(path):
    # Reads a list file (one entry per line) and returns a set of lowercase
    # strings. Blank lines and lines starting with '#' are ignored so the
    # list files can contain comments.
    entries = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip().lower()          # remove spaces/newline, make lowercase
            if line and not line.startswith("#"):  # skip blanks and comments
                entries.add(line)
    return entries


class Rule:
    # A condition-action rule ("if condition then action"), as in the book.
    # condition: a function that takes the interpreted state and returns True/False
    # action:    the action to return when the condition is True
    # name:      a human-readable label (useful for logging and the demo)
    def __init__(self, name, condition, action):
        self.name = name
        self.condition = condition
        self.action = action

    def __repr__(self):
        return f"Rule({self.name} -> {self.action})"


class SimpleReflexSpamAgent:
    # The SIMPLE-REFLEX-AGENT. Calling agent(percept) runs one
    # percept -> action cycle.

    def __init__(self, allow_list, restrict_list, bad_words, threshold=5):
        # ---- Persistent knowledge of the agent ----
        # These are the "persistent" variables from Figure 2.10.
        self.allow_list = {d.lower() for d in allow_list}        # safe domains
        self.restrict_list = {d.lower() for d in restrict_list}  # always-spam domains
        self.bad_words = {w.lower() for w in bad_words}          # spam vocabulary
        self.threshold = threshold  # spam if bad-word count is MORE THAN this (> 5)

        # ---- The condition-action rules ----
        # Rules are checked IN ORDER and the first matching rule wins.
        # The order encodes the priorities from the assignment:
        #   1. allow list beats everything ("regardless of its contents")
        #   2. restrict list beats the bad-word rule ("regardless of its contents")
        #   3. more than 5 bad words -> spam (only reached if not allow-listed)
        #   4. default -> normal email
        self.rules = [
            Rule("sender domain is on allow list",
                 lambda s: s["on_allow_list"], MOVE_TO_EMAIL),
            Rule("sender domain is on restrict list",
                 lambda s: s["on_restrict_list"], MOVE_TO_SPAM),
            Rule(f"more than {threshold} bad words in body",
                 lambda s: s["bad_word_count"] > self.threshold, MOVE_TO_SPAM),
            Rule("default: no spam rule matched",
                 lambda s: True, MOVE_TO_EMAIL),
        ]

        # Remembers which rule fired last time (only for logging/explaining;
        # it is NOT used in decisions, so the agent stays a simple reflex agent).
        self.last_rule = None

    @classmethod
    def from_files(cls, allow_path=None, restrict_path=None, bad_words_path=None, threshold=5):
        # Convenience constructor: builds the agent from the three list files.
        # If a path is not given, the default file in spam_agent/data/ is used.
        return cls(
            load_list(allow_path or DATA_DIR / "allow_list.txt"),
            load_list(restrict_path or DATA_DIR / "restrict_list.txt"),
            load_list(bad_words_path or DATA_DIR / "bad_words.txt"),
            threshold,
        )

    # ------------------------------------------------------------------
    # SIMPLE-REFLEX-AGENT(percept)
    # ------------------------------------------------------------------
    def __call__(self, percept):
        state = self.interpret_input(percept)        # state  <- INTERPRET-INPUT(percept)
        rule = self.rule_match(state, self.rules)    # rule   <- RULE-MATCH(state, rules)
        self.last_rule = rule                        # (remember for logging only)
        return rule.action                           # action <- rule.ACTION; return action

    # ------------------------------------------------------------------
    # INTERPRET-INPUT(percept)
    # Turns the raw percept (bytes of an .eml file) into an abstract
    # state description containing only what the rules need.
    # ------------------------------------------------------------------
    def interpret_input(self, percept):
        # Accept either bytes or str (str is converted to bytes).
        if isinstance(percept, str):
            percept = percept.encode("utf-8")

        # SENSOR: parse the .eml file into headers + body parts.
        msg = email.message_from_bytes(percept, policy=policy.default)

        # Get the sender's domain from the "From:" header.
        domain = self.sender_domain(msg)

        # Get all readable body text (decoded), including text attachments.
        body = self.readable_text(msg)

        # Count how many bad words appear in the body.
        bad_count = self.count_bad_words(body)

        # The abstract state used by the rules.
        return {
            "domain": domain,
            "on_allow_list": self.domain_in(domain, self.allow_list),
            "on_restrict_list": self.domain_in(domain, self.restrict_list),
            "bad_word_count": bad_count,
        }

    # ------------------------------------------------------------------
    # RULE-MATCH(state, rules)
    # Returns the FIRST rule whose condition is true for this state.
    # ------------------------------------------------------------------
    @staticmethod
    def rule_match(state, rules):
        for rule in rules:
            if rule.condition(state):
                return rule
        # Unreachable, because the last rule is always True,
        # but kept as a safety net.
        raise ValueError("no rule matched")

    # ================= Helper functions used by INTERPRET-INPUT ==========

    @staticmethod
    def sender_domain(msg):
        # Extracts the domain from the From header.
        # Example: "Bob <bob@Mail.Seneca.ca>" -> "mail.seneca.ca"
        address = parseaddr(str(msg.get("From", "")))[1].lower()
        if "@" not in address:
            return ""                         # no valid sender -> empty domain
        return address.rsplit("@", 1)[1].strip(" >.")

    @staticmethod
    def domain_in(domain, domain_list):
        # True if the domain is in the list OR is a subdomain of a listed domain.
        # Example: "mail.seneca.ca" matches "seneca.ca",
        #          but "notseneca.ca" does NOT match "seneca.ca".
        if not domain:
            return False
        return any(domain == d or domain.endswith("." + d) for d in domain_list)

    @staticmethod
    def readable_text(msg):
        # Walks through every MIME part of the email and collects the text
        # of every part whose main type is "text" (text/plain, text/html, ...).
        # This includes attachments of type text, as the assignment allows.
        # get_content() automatically decodes base64 / quoted-printable and
        # charsets. Parts that cannot be decoded (e.g. encrypted or broken)
        # are skipped, because the agent cannot read them.
        pieces = []
        for part in msg.walk():
            if part.is_multipart():               # containers have no text themselves
                continue
            if part.get_content_maintype() != "text":
                continue                          # images, pdf, etc. are unreadable
            try:
                content = part.get_content()
            except Exception:
                continue                          # undecodable part -> ignore it
            if part.get_content_subtype() == "html":
                content = re.sub(r"<[^>]+>", " ", content)  # strip HTML tags
            pieces.append(content)
        return "\n".join(pieces)

    def count_bad_words(self, text):
        # Counts EVERY occurrence of a bad word (repeats count, so
        # "free free free" = 3). Matching is case-insensitive and on whole
        # words only ("freedom" does not count as "free").
        # Entries with a space (e.g. "act now") are counted as phrases.
        text = text.lower()
        words = re.findall(r"[a-z0-9']+", text)   # split text into words
        count = 0
        for bad in self.bad_words:
            if " " in bad:
                # multi-word phrase: count whole-phrase occurrences
                count += len(re.findall(r"\b" + re.escape(bad) + r"\b", text))
            else:
                # single word: count matching words
                count += words.count(bad)
        return count
