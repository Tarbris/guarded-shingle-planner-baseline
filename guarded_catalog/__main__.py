"""JSONL CLI. One response per line; rejected commands do not change state."""

import json
import sys

from .catalog import ExactCatalog


def dispatch(catalog, command):
    if not isinstance(command, dict) or not isinstance(command.get("op"), str):
        raise ValueError("command must be an object with op")
    op = command["op"]
    if op == "put":
        if set(command) != {"op", "id", "text", "priority", "protected"}:
            raise ValueError("put fields differ")
        catalog.put(command["id"], command["text"], command["priority"], command["protected"])
        return None
    if op == "delete":
        if set(command) != {"op", "id"}:
            raise ValueError("delete fields differ")
        return catalog.delete(command["id"])
    if op in {"snapshot", "exact_plan"}:
        if set(command) != {"op"}:
            raise ValueError("query fields differ")
        return getattr(catalog, op)()
    raise ValueError("unknown operation")


def main():
    catalog = ExactCatalog()
    for line in sys.stdin:
        try:
            result = dispatch(catalog, json.loads(line))
            output = {"ok": True, "result": result}
        except (ValueError, TypeError, KeyError) as exc:
            output = {"ok": False, "error": "invalid-command", "detail": str(exc)}
        print(json.dumps(output, ensure_ascii=False, sort_keys=True, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
