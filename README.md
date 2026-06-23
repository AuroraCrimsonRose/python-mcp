# python-mcp

python-mcp is a lightweight, modular tool execution runtime written in Python.

It was an experimental framework for registering and executing modular “tools” (functions or components) through a central runtime and registry system. The goal was to explore simple patterns for tool orchestration and execution, with ideas that could later evolve toward MCP-style integrations.

## Overview

The project explores:

* A structured tool execution system
* Centralized tool registry and discovery
* Isolated runtime execution model
* Pluggable architecture for future transport layers
* Early concepts for standardizing tool interfaces

## Architecture

The system was designed around a few core components:

* **Tools**: Self-contained functions or modules that perform a single task
* **Registry**: Central system for registering and resolving tools
* **Runtime**: Executes tools with basic isolation and normalization
* **Transport (planned)**: Intended support for stdio, HTTP, and WebSocket interfaces

## Status

This project is no longer under active development.

It was abandoned after the original use case no longer applied, and development direction shifted. No further updates, maintenance, or expansion are planned.

The codebase remains as a reference implementation and experimental archive.

Expect incomplete features, shifting architecture, and non-production-ready behavior throughout.

## Notes

* This is an experimental prototype, not a production framework
* APIs and structure were subject to frequent change during development
* The transport layer was never fully implemented
* The design reflects early-stage exploration rather than a finalized system

## License

This project is released under the MIT License.

You are free to use, modify, fork, redistribute, and build upon it.
See the LICENSE file for full details.
