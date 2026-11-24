# Project Instructions

- Follow the requirements in `spec.md`, the decisions in `plan.md`, the order in `tasks.md`, and the project structures in `backend-structure.md` and `frontend-structure.md`.
- Before implementing a task, read the relevant requirements, decisions, tasks, and structure documents. Do not assume that referenced documents have already been loaded.
- Respect the approved project structure.
- Inspect existing files and patterns before making changes.
- Implement only the assigned task, and stop to request approval when decisions are unresolved or architectural changes are needed.
- Do not introduce a new technology or major dependency without approval.
- Run relevant existing tests after each task. Run the full test suite when required by the project's testing policy or when changes may affect broader functionality. Report the test commands and results, and suggest additional tests when needed.
- Summarize the files and changes after each task.
- Add concise and meaningful code comments to explain non-obvious logic, important business rules, edge cases, and complex implementations. Use section comments to organize code into logical sections when helpful. Avoid unnecessary comments that simply repeat what the code already expresses, and keep comments accurate and up to date.
- Use `uv` as the package and virtual environment manager for the Python backend. Manage dependencies through `uv` commands (`uv add`, `uv remove`, `uv sync`), declare dependencies in `pyproject.toml`, and keep `uv.lock` synchronized. Use `uv run` to execute Python commands and tools. Do not use `pip` directly to install or manage dependencies.