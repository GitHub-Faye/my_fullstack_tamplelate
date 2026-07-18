## Agent skills

### Issue tracker

Issues tracked via GitHub Issues using the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Five canonical triage roles mapped to default label strings. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — root `CONTEXT.md` + `docs/adr/`. See `docs/agents/domain.md`.


# Agent Workspace Rules & Tool Usage

## Codebase Memory MCP (Primary Exploration Tool)
The codebase-memory-mcp server is fully indexed for this repository. 
**Always use MCP tools as the PRIMARY method for code exploration** before falling back to raw file reads or grep.

Preferred exploration order:
1. Use `search_graph`, `trace_call_path`, `get_architecture`, `get_code_snippet` etc. first.
2. Only use `view_file` or `grep_search` when the graph cannot provide the needed context.
3. Goal: Minimize token usage — never read entire large files if a snippet or graph query suffices.
