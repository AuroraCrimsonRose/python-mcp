# python-mcp

**python-mcp** is a lightweight, modular tool execution runtime written in Python.

It enables registration and dynamic execution of tools (functions or modules) with a focus on simplicity, extensibility, and readiness for future MCP-style integrations. For development and rapid iteration, a local language model assists with debugging and code generation.

---

## Features

- **Structured tool system**: Define and run discrete tools with minimal overhead
- **Central tool registry**: Discover, register, and manage tools from a single place
- **Isolated execution runtime**: Handles invocation, error management, and normalization
- **Extensible transport**: Designed to support stdio, HTTP, and WebSocket interfaces in the future

---

## Core Concepts

### Tools

A **tool** is a function or module dedicated to a specific task.

Key attributes:

- `name`: Tool identifier (string)
- `description`: Brief description
- `execute`: Callable function to run the tool
- `input schema` (optional): Schema for validating input

**Example:**

```python
def example_tool(input: dict):
    return {"result": "ok"}

TOOL = {
    "name": "example_tool",
    "description": "Example tool",
    "execute": example_tool,
}
```

---

### Registry

The **registry** provides:

- Tool registration (at startup or dynamically)
- Listing of all available tools
- Resolution and execution lookup by name

---

### Runtime

The **runtime** manages:

- Tool invocation and error isolation
- Input/output normalization
- Execution flow, including optional pre/post hooks

---

### Transport (Planned)

Support for multiple interfaces is on the roadmap:

- stdio (for local MCP clients)
- HTTP API (remote integration)
- WebSocket (streaming & interactive sessions)

---

## Project Structure

Recommended directory layout:

```
core/         # Core framework logic, registries, interfaces
runtime/      # Execution flow, runners, error handling
registry/     # Tool registration and discovery utilities
protocol/     # Data structure definitions and schemas
transport/    # (Future) Interface implementations
tools/        # Tool modules
filesystem/   # Example tool domain
system/       # Example tool domain
network/      # Example tool domain
server.py     # Main entry point
```

---

## Getting Started

1. **Create a virtual environment:**

   ```sh
   python -m venv .venv
   ```

2. **Activate the environment:**

   - Windows:  
     `.venv\Scripts\activate`
   - Linux/macOS:  
     `source .venv/bin/activate`

3. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Run the server:**

   ```sh
   python server.py
   ```

---

## Adding a Tool

- Place a Python file with your tool in the `tools/` directory.
- Define your tool as shown in the example above.
- Register your tool with the registry system.

---

## Notes

- This project is in early development: expect rapid iteration and structural changes.
- Tool definitions and the registry API may evolve.
- Transport layer is currently unimplemented.
- A local language model is used during development for coding, debugging, and accelerating iteration.

---

## Roadmap

- [ ] Tool schema validation
- [ ] Automatic tool discovery
- [ ] MCP compatibility layer
- [ ] Transport abstraction (stdio / HTTP)
- [ ] Async execution support

---

Contributions and feedback are welcome!
