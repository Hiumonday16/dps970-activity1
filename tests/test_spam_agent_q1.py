# ------------------------------------------------------------------------
# test_spam_agent_q1.py
# Automated tests for Question 1 (spam filter agent).
# Run from the project root with:   pytest -v
# ------------------------------------------------------------------------

from pathlib import Path

import pytest

from spam_agent.agent_q1 import SimpleReflexSpamAgent, MOVE_TO_SPAM, MOVE_TO_EMAIL, load_list
from spam_agent.environment_q1 import run

# Folder that holds the test .eml files (the test data).
EMAILS = Path(__file__).parent / "emails"


@pytest.fixture
def agent():
    # A fresh agent built from the default list files in spam_agent/data/.
    # pytest gives this to any test function that has an "agent" parameter.
    return SimpleReflexSpamAgent.from_files()


# ---- Expected result for every test email --------------------------------
# (file name, expected action, why)
CASES = [
    ("01_allow_clean.eml",        MOVE_TO_EMAIL, "allowed domain, clean body"),
    ("02_allow_many_bad.eml",     MOVE_TO_EMAIL, "allow list overrides many bad words"),
    ("03_restrict_clean.eml",     MOVE_TO_SPAM,  "restrict list overrides clean body"),
    ("04_unknown_clean.eml",      MOVE_TO_EMAIL, "unknown domain, clean body"),
    ("05_unknown_5_bad.eml",      MOVE_TO_EMAIL, "exactly 5 bad words is NOT more than 5"),
    ("06_unknown_6_bad.eml",      MOVE_TO_SPAM,  "6 bad words is more than 5"),
    ("07_base64_body.eml",        MOVE_TO_SPAM,  "bad words hidden in a base64 body"),
    ("08_text_attachment.eml",    MOVE_TO_SPAM,  "bad words only in a text attachment"),
    ("09_subdomain_allow.eml",    MOVE_TO_EMAIL, "subdomain of an allowed domain"),
    ("10_subdomain_restrict.eml", MOVE_TO_SPAM,  "subdomain of a restricted domain"),
    ("11_uppercase_bad.eml",      MOVE_TO_SPAM,  "matching is case-insensitive"),
    ("12_both_lists.eml",         MOVE_TO_EMAIL, "domain on both lists: allow wins"),
    ("13_lookalike_domain.eml",   MOVE_TO_SPAM,  "notgithub.com is not github.com"),
    ("14_html_body.eml",          MOVE_TO_SPAM,  "bad words inside an HTML body"),
    ("15_binary_attachment.eml",  MOVE_TO_EMAIL, "non-text attachment is not read"),
    ("16_quoted_printable.eml",   MOVE_TO_SPAM,  "quoted-printable body is decoded"),
    ("17_phrases.eml",            MOVE_TO_SPAM,  "multi-word phrases are counted"),
    ("18_similar_words.eml",      MOVE_TO_EMAIL, "'freedom' is not 'free' (whole words only)"),
]


# ---- 1. Every test email is classified correctly -------------------------
# parametrize runs this one test once per row in CASES.
@pytest.mark.parametrize("filename, expected, reason", CASES)
def test_classification(agent, filename, expected, reason):
    percept = (EMAILS / filename).read_bytes()
    assert agent(percept) == expected, reason


# ---- 2. Every .eml file in the folder has an expected result -------------
def test_every_email_has_a_case():
    on_disk = {p.name for p in EMAILS.glob("*.eml")}
    in_cases = {c[0] for c in CASES}
    assert on_disk == in_cases


# ---- 3. Bad-word counting (unit tests of INTERPRET-INPUT helpers) --------
def test_count_repeats_case_and_whole_words(agent):
    assert agent.count_bad_words("free FREE Free") == 3      # repeats + case
    assert agent.count_bad_words("freedom freely") == 0      # whole words only
    assert agent.count_bad_words("act now, ACT NOW") == 2    # phrases


def test_threshold_boundary():
    # Small custom agent: only one bad word, "spam".
    a = SimpleReflexSpamAgent(allow_list=[], restrict_list=[], bad_words=["spam"])
    five = b"From: x@test.com\n\nspam spam spam spam spam"
    six = b"From: x@test.com\n\nspam spam spam spam spam spam"
    assert a(five) == MOVE_TO_EMAIL     # 5 is not MORE than 5
    assert a(six) == MOVE_TO_SPAM       # 6 is more than 5


# ---- 4. Domain extraction and matching -----------------------------------
def test_sender_domain_parsing(agent):
    state = agent.interpret_input(b"From: Bob <Bob@Mail.Example.COM>\n\nhi")
    assert state["domain"] == "mail.example.com"


def test_missing_from_header_is_not_allowed(agent):
    # No From header -> no domain -> cannot be on the allow list.
    body = b"Subject: hi\n\n" + b"free " * 6
    assert agent(body) == MOVE_TO_SPAM


def test_domain_matching():
    assert SimpleReflexSpamAgent.domain_in("a.b.com", {"b.com"})
    assert SimpleReflexSpamAgent.domain_in("b.com", {"b.com"})
    assert not SimpleReflexSpamAgent.domain_in("notb.com", {"b.com"})
    assert not SimpleReflexSpamAgent.domain_in("", {"b.com"})


# ---- 5. RULE-MATCH reports which rule fired ------------------------------
def test_rule_that_fired(agent):
    agent((EMAILS / "02_allow_many_bad.eml").read_bytes())
    assert agent.last_rule.name == "sender domain is on allow list"
    agent((EMAILS / "03_restrict_clean.eml").read_bytes())
    assert agent.last_rule.name == "sender domain is on restrict list"


# ---- 6. List files load correctly (comments/blank lines ignored) ---------
def test_load_list_ignores_comments(tmp_path):
    f = tmp_path / "list.txt"
    f.write_text("# comment\n\nExample.COM\n  other.org  \n", encoding="utf-8")
    assert load_list(f) == {"example.com", "other.org"}


# ---- 7. End-to-end: environment puts files in the right folders ----------
def test_environment_sorts_files(agent, tmp_path):
    # tmp_path is a temporary folder pytest creates and deletes for us.
    run(EMAILS, tmp_path, agent)
    spam = {p.name for p in (tmp_path / "spam").iterdir()}
    normal = {p.name for p in (tmp_path / "email").iterdir()}

    expected_spam = {f for f, action, _ in CASES if action == MOVE_TO_SPAM}
    expected_email = {f for f, action, _ in CASES if action == MOVE_TO_EMAIL}
    assert spam == expected_spam
    assert normal == expected_email
    assert not spam & normal          # no email is in both folders


def test_environment_move_mode(agent, tmp_path):
    # With move=True the inbox should be empty afterwards.
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "a.eml").write_bytes((EMAILS / "06_unknown_6_bad.eml").read_bytes())
    run(inbox, tmp_path / "out", agent, move=True)
    assert not any(inbox.iterdir())
    assert (tmp_path / "out" / "spam" / "a.eml").exists()
