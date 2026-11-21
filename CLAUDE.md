# Rules for AI agents

## General rules

- Running, rebuilding, restarting existing containers or running versions is allowed.
- Creating, uploading or modifying to PyPI, GitHub or any third-party service is NOT allowed under any circumstances.
- Updating the documentation (doc comments, comments, markdown files) is disallowed.
- Always follow the existing code formatting, styling, especially the naming conventions, whitespaces, wording. When unsure, refer to existing code.
- When unsure, refer to the webui folder for code conventions.
- Modifying the README.md, CONTRIBUTING.md, CLAUDE.md or any other agent, IDE config or similar file is forbidden unless the human asked for it.

## Git rules

- Creating git commits is disallowed and should only ever be done by the human in the loop.
- Signing/coauthoring commits as Claude is disallowed. This is a human led project, AI agents are only used as engineering guides, ideators, code reviewers, not developers.
- Creating branches is not allowed unless explicitly requested by the human.

## Testing

- Non-critical or not too complex parts of the code are manually tested.
- Always ask the human for permission before adding tests.