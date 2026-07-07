# Context Awareness Subsystem

The Context subsystem tracks active conversation variables and resolves natural language references (e.g. "it", "the first one", "the folder") in user commands *before* they are processed by the core Assistant. It operates entirely in-memory and clears all session states automatically when a conversation ends.

## Architecture

```
User Voice Input ──> ReferenceResolver ──[Resolved Command]──> Assistant/Dispatcher
                           ▲
                           │ reads state
                     ContextManager (ContextState & TemporaryMemory)
```

- **ContextManager**: Coordinates updates to `ContextState` (persisting files, folders, search results, intents, capabilities, execution results, and confirmations) and tracks `TemporaryMemory`.
- **ReferenceResolver**: Evaluates plain text commands against context fields and replaces ambiguous terms:
  - **Pronouns** (`it`, `that`, `this`, `those`): Replaces with the active file or folder. If both are set, identifies ambiguity and returns a clarification request.
  - **Ordinals** (`the first one`, `the second one`, `the last file/one`): Replaces with the corresponding element from search results.
  - **Nouns** (`the folder`, `the document`, `the image`): Replaces with context folders or files matching specific document/image extensions.
- **TemporaryMemory**: Stores session-scoped keys and values, which are purged when the conversation terminates.

## Resolution Rules

| Reference | Target in ContextState | Failure / Ambiguity Response |
|---|---|---|
| `it` / `that` / `this` / `those` | `current_file` (if folder is empty) OR `current_folder` (if file is empty) | Requests clarification if both are set or both are empty. |
| `the first one` | `current_search_results[0]` | Requests clarification if search results list is empty. |
| `the second one` | `current_search_results[1]` | Requests clarification if search results list has fewer than 2 items. |
| `the last file` / `the last one` | `current_search_results[-1]` (or fallback to `current_file`) | Requests clarification if both are empty. |
| `the folder` | `current_folder` | Requests clarification if empty. |
| `the document` | `current_file` (if document extension) OR search results (if exactly one document exists) | Requests clarification if multiple or no documents exist in context. |
| `the image` | `current_file` (if image extension) OR search results (if exactly one image exists) | Requests clarification if multiple or no images exist in context. |

## Usage

### Updating Context & Resolving Command

```python
from voice.context import ContextManager

# 1. Initialize Context Manager
cm = ContextManager()

# 2. Update context state with last search results
cm.update(
    current_search_results=["index.html", "script.js", "style.css", "image.png"],
    current_folder="projects/my_web_app"
)

# 3. Resolve ordinals
result = cm.resolve_references("delete the second one")
print(result.resolved_command)  # Output: "delete script.js"
print(result.requires_clarification)  # Output: False

# 4. Resolve pronouns (ambiguity check)
result = cm.resolve_references("open it")
# Since current_folder is set and search results exist (we don't have current_file set yet,
# but if both current_file and current_folder were set, it would be ambiguous):
# Let's say we set current_file first:
cm.update(current_file="index.html")
result = cm.resolve_references("copy it")
# Ambiguous! Both file and folder are set:
print(result.requires_clarification)  # Output: True
print(result.clarification_prompt)    # Output: "I see both a file ('index.html') and a folder ('projects/my_web_app') in context. Which one did you mean?"
```
