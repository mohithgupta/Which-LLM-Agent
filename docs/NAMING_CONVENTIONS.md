# Documentation Naming Conventions

This document outlines the naming conventions and folder structure standards for the LLM Agents Search documentation.

## Folder Structure

The documentation is organized into category-based subfolders within the `docs/` directory:

```
docs/
├── index.md                           # Homepage
├── NAMING_CONVENTIONS.md             # This file
├── starter_ai_agents/                # Basic AI agent implementations
├── advanced_ai_agents/               # Complex AI agent patterns
├── multi_agent_teams/                # Multi-agent system documentation
├── voice_ai_agents/                  # Voice-enabled AI agents
├── mcp_ai_agents/                    # Model Context Protocol agents
├── rag_agents/                       # Retrieval-Augmented Generation agents
├── memory_tutorials/                 # Memory and context management
└── chat_with_x/                      # Chat integration tutorials
```

## File Naming Rules

### Category Folders

- **Format**: `lowercase_with_underscores`
- **Examples**: `starter_ai_agents`, `multi_agent_teams`
- **Purpose**: Group related documentation by topic or agent type

### Documentation Files

- **Format**: `lowercase_with_underscores.md`
- **Examples**: `agent_setup.md`, `configuration_guide.md`
- **Purpose**: Individual documentation pages within categories

### Index Files

Each category folder should contain an `index.md` file that serves as the landing page for that section.

## Agent Page Naming

When creating documentation for individual agents:

1. **Use descriptive names**: `web_search_agent.md` instead of `agent1.md`
2. **Follow lowercase convention**: Always use lowercase with underscores
3. **Include the agent type**: Make it clear what category the agent belongs to
4. **Keep it concise**: Prefer shorter, clearer names

## MkDocs Navigation

The `mkdocs.yml` file uses these naming conventions to structure the navigation menu. Ensure file names match the nav configuration.

## Best Practices

1. **Be consistent**: Always follow the established patterns
2. **Use clear, descriptive names**: Make content self-explanatory
3. **Avoid special characters**: Stick to alphanumeric and underscores
4. **Keep names short**: Long names are harder to read and link to
5. **Group logically**: Place files in the most appropriate category folder

## Adding New Content

When adding new documentation:

1. Choose the appropriate category folder
2. Create a new `.md` file following the naming conventions
3. Add the file to the `mkdocs.yml` navigation
4. Update the category's `index.md` if needed

## Examples

**Good names:**
- `web_search_agent.md`
- `memory_management.md`
- `voice_integration.md`

**Avoid:**
- `Agent1.md` (use lowercase)
- `my-new-file.md` (use underscores, not hyphens)
- `VeryLongDescriptiveFileNameThatIsHardToRead.md` (too long)
