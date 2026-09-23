"""Executable BEFORE/AFTER proof: edit_file CRLF preservation, '-- ' diff deletion, and
string-flag coercion (preview_only="false").

Run once per world:
  OLD (git HEAD, pre-wave):  PYTHONPATH=/tmp/proof_old_abstractcore python ab_edit_file_and_coercion.py old
  NEW (working tree):        python ab_edit_file_and_coercion.py new

(Worktree if missing:  git -C abstractcore worktree add /tmp/proof_old_abstractcore HEAD)
Artifacts land next to this script as ab_results_<world>.json — byte-level, diffable.
"""
import json
import sys
import tempfile
from pathlib import Path

WORLD = sys.argv[1]

import abstractcore  # noqa: E402
from abstractcore.tools.common_tools import edit_file  # noqa: E402

assert (WORLD == "old") == ("/tmp/proof_old_abstractcore" in abstractcore.__file__), (
    f"world mismatch: {WORLD} but loaded {abstractcore.__file__}"
)

results = {"world": WORLD, "abstractcore_file": abstractcore.__file__}
tmp = Path(tempfile.mkdtemp(prefix=f"ab_{WORLD}_"))

# ---- Proof 1: CRLF file survives an edit? ----
p1 = tmp / "settings.ini"
p1.write_bytes(b"[app]\r\nmode = debug\r\nlevel = 3\r\n")
edit_file(str(p1), "mode = debug", "mode = production")
b1 = p1.read_bytes()
results["crlf_edit"] = {
    "bytes_after": b1.decode("utf-8").replace("\r", "\\r").replace("\n", "\\n"),
    "crlf_preserved": b"\r\n" in b1 and b"mode = production\r\n" in b1,
    "silently_rewritten_to_lf": b"\r\n" not in b1,
}

# ---- Proof 2: unified diff deleting a SQL comment line ('-- ' prefix) ----
p2 = tmp / "query.sql"
p2.write_text("SELECT 1;\n-- old comment\nSELECT 2;\n")
patch = (
    "--- a/query.sql\n+++ b/query.sql\n@@ -1,3 +1,2 @@\n"
    " SELECT 1;\n"
    "--- old comment\n"
    " SELECT 2;\n"
)
msg2 = edit_file(str(p2), patch)
results["dashdash_diff"] = {
    "tool_message_head": str(msg2)[:160],
    "applied": p2.read_text() == "SELECT 1;\nSELECT 2;\n",
    "file_after": p2.read_text(),
}

# ---- Proof 3: preview_only="false" (string) through the dispatch path ----
# Models on prompted/XML tool formats send string flags. Old dispatch passed the raw string
# through; in Python bool("false") is True -> edit previews and SILENTLY DISCARDS the change
# while the agent believes it edited the file.
p3 = tmp / "config.py"
p3.write_text("retries = 3\n")
try:
    from abstractcore.tools.core import ToolCall
    from abstractcore.tools.registry import ToolRegistry

    reg = ToolRegistry()
    reg.register(edit_file)
    call = ToolCall(
        name="edit_file",
        arguments={"file_path": str(p3), "pattern": "retries = 3",
                   "replacement": "retries = 5", "preview_only": "false"},
    )
    out = reg.execute_tool(call)
    out_msg = str(getattr(out, "output", None) or getattr(out, "result", None) or out)[:160]
except Exception as e:  # registry API drift between worlds
    out_msg = f"registry error: {e}"
results["string_flag_coercion"] = {
    "tool_message_head": out_msg,
    "file_actually_edited": p3.read_text() == "retries = 5\n",
    "file_after": p3.read_text(),
}

out_path = Path(__file__).parent / f"ab_results_{WORLD}.json"
out_path.write_text(json.dumps(results, indent=1))
print(json.dumps(results, indent=1))
print("WROTE", out_path)
