"""The published baseline deliberately contains no near-duplicate planner."""

import re


_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z", re.ASCII)
_TOKEN = re.compile(r"[A-Za-z0-9]+", re.ASCII)


def tokenize(text):
    """ASCII alphanumeric runs, lowercased; every other character separates."""
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("text must be valid Unicode") from exc
    return [token.lower() for token in _TOKEN.findall(text)]


def _identifier(value):
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise ValueError("invalid document id")


class ExactCatalog:
    """In-memory, single-threaded current document state.

    put replaces the whole existing document. Values are scalar and snapshot
    allocates fresh dictionaries, so callers cannot mutate stored state.
    """

    def __init__(self):
        self._documents = {}

    def put(self, doc_id, text, priority=0, protected=False):
        _identifier(doc_id)
        tokenize(text)
        if type(priority) is not int or not -(2**31) <= priority < 2**31:
            raise ValueError("priority must be a signed 32-bit integer")
        if type(protected) is not bool:
            raise ValueError("protected must be boolean")
        self._documents[doc_id] = {
            "id": doc_id, "text": text, "priority": priority,
            "protected": protected,
        }

    def delete(self, doc_id):
        _identifier(doc_id)
        return self._documents.pop(doc_id, None) is not None

    def snapshot(self):
        return [dict(self._documents[key]) for key in sorted(self._documents)]

    def exact_plan(self):
        """Group equal token sequences, with all empty documents singleton.

        The original exact API chooses the smallest (priority, id). It has no
        protected-document constraint. New APIs must not change this behavior.
        """
        buckets = {}
        for doc in self.snapshot():
            tokens = tuple(tokenize(doc["text"]))
            key = ("tokens", tokens) if tokens else ("empty", doc["id"])
            buckets.setdefault(key, []).append(doc)
        groups = []
        for documents in buckets.values():
            winner = min(documents, key=lambda doc: (doc["priority"], doc["id"]))
            groups.append({
                "representative": winner["id"],
                "members": sorted(doc["id"] for doc in documents),
            })
        return {"groups": sorted(groups, key=lambda group: group["representative"])}
