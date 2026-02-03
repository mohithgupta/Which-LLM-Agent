#!/usr/bin/env python3
"""
Homepage Generator

This script generates a homepage with agent cards organized by category.
It reads agent metadata from markdown files in the output/ directory and
creates a visually appealing card grid layout using Material theme components.

The generated homepage uses Material for MkDocs card components and
custom CSS classes for styling.
"""

import argparse
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import quote


def parse_simple_yaml_frontmatter(yaml_text: str) -> Dict[str, Any]:
    """
    Parse simple YAML frontmatter without external dependencies.

    This is a simplified YAML parser that handles the specific format
    used in markdown frontmatter (key: value pairs).

    Args:
        yaml_text: YAML text to parse

    Returns:
        Dictionary of parsed key-value pairs
    """
    result = {}
    for line in yaml_text.split('\n'):
        line = line.strip()
        if ':' in line and not line.startswith('#'):
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            result[key] = value
    return result


@dataclass
class AgentMetadata:
    """
    Represents metadata extracted from an agent markdown file.

    Attributes:
        title: The agent name/title
        description: Optional agent description
        category: The category this agent belongs to
        url: The GitHub repository URL
        file_path: Relative path to the markdown file
    """
    title: str
    description: Optional[str] = None
    category: str = ""
    url: str = ""
    file_path: str = ""


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration for the script.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at {log_level.upper()} level")
    logger.debug("Detailed debug logging enabled")
    return logger


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the script.

    Returns:
        Parsed arguments namespace
    """
    logger = logging.getLogger(__name__)
    logger.debug("Parsing command-line arguments")

    parser = argparse.ArgumentParser(
        description="Generate homepage with agent card grid from markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default settings
  %(prog)s

  # Specify custom output directory
  %(prog)s --output-dir custom_output

  # Specify custom output file
  %(prog)s --output docs/index.md

  # Dry run to test without writing files
  %(prog)s --dry-run

  # Enable debug logging
  %(prog)s --debug
        """
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory containing markdown files (default: output)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="docs/index.md",
        help="Output file path for generated homepage (default: docs/index.md)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate homepage but don't write output file"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging for troubleshooting"
    )

    args = parser.parse_args()
    logger.debug(
        f"Arguments parsed: output_dir={args.output_dir}, "
        f"output={args.output}, dry_run={args.dry_run}, "
        f"debug={args.debug}"
    )
    return args


def gather_agent_metadata(output_dir: str) -> Dict[str, List[AgentMetadata]]:
    """
    Scan the output directory and extract metadata from all markdown files.

    This function recursively scans the output directory for markdown files,
    parses their YAML frontmatter, and organizes the metadata by category.

    Args:
        output_dir: Path to the output directory containing markdown files

    Returns:
        Dictionary mapping category names to lists of AgentMetadata objects

    Raises:
        FileNotFoundError: If the output directory does not exist
        ValueError: If no valid markdown files are found
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Scanning output directory: {output_dir}")

    output_path = Path(output_dir)
    if not output_path.exists():
        logger.error(f"Output directory not found: {output_dir}")
        raise FileNotFoundError(f"Output directory not found: {output_dir}")

    # Dictionary to store agents by category
    agents_by_category: Dict[str, List[AgentMetadata]] = {}

    # Track statistics
    total_files = 0
    parsed_successfully = 0
    parse_errors = 0

    # Recursively find all markdown files
    markdown_files = list(output_path.rglob("*.md"))
    total_files = len(markdown_files)

    logger.info(f"Found {total_files} markdown files to process")

    if total_files == 0:
        logger.warning("No markdown files found in output directory")
        raise ValueError("No markdown files found in output directory")

    # Process each markdown file
    for md_file in markdown_files:
        try:
            logger.debug(f"Processing file: {md_file}")

            # Read file content and parse frontmatter
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract YAML frontmatter (between --- delimiters)
            frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)

            if not frontmatter_match:
                logger.warning(f"No frontmatter found in {md_file}, skipping")
                parse_errors += 1
                continue

            # Parse YAML frontmatter
            yaml_text = frontmatter_match.group(1)
            try:
                metadata = parse_simple_yaml_frontmatter(yaml_text)
            except Exception as e:
                logger.warning(f"Invalid YAML in {md_file}: {e}, skipping")
                parse_errors += 1
                continue

            # Extract metadata fields
            title = metadata.get('title', '')
            description = metadata.get('description', None)
            category = metadata.get('category', 'Uncategorized')
            url = metadata.get('url', '')

            # Validate required fields
            if not title:
                logger.warning(f"No title found in {md_file}, skipping")
                parse_errors += 1
                continue

            # Create AgentMetadata object
            agent = AgentMetadata(
                title=title,
                description=description,
                category=category,
                url=url,
                file_path=str(md_file.relative_to(output_path))
            )

            # Add to category group
            if category not in agents_by_category:
                agents_by_category[category] = []

            agents_by_category[category].append(agent)
            parsed_successfully += 1

            logger.debug(
                f"Extracted metadata for '{title}' "
                f"(category: {category}, description: {bool(description)})"
            )

        except Exception as e:
            logger.error(f"Error processing {md_file}: {e}")
            parse_errors += 1
            continue

    # Log summary statistics
    total_agents = sum(len(agents) for agents in agents_by_category.values())
    logger.info(f"Processing complete:")
    logger.info(f"  Total files scanned: {total_files}")
    logger.info(f"  Successfully parsed: {parsed_successfully}")
    logger.info(f"  Parse errors: {parse_errors}")
    logger.info(f"  Categories found: {len(agents_by_category)}")
    logger.info(f"  Total agents: {total_agents}")

    if total_agents == 0:
        logger.warning("No valid agent metadata extracted")
        raise ValueError("No valid agent metadata found")

    return agents_by_category


def generate_agent_card(agent: AgentMetadata, category: str) -> str:
    """
    Generate markdown for a single agent card.

    Args:
        agent: AgentMetadata object containing agent information
        category: Category name for the agent

    Returns:
        Markdown string for the agent card
    """
    # Create relative link from docs/index.md to agent page
    # Agent files are in output/<category>/<agent>.md
    # We need to link to ../output/<category>/<agent>.md from docs/index.md
    # Normalize path separators to forward slashes for web URLs
    # URL-encode spaces and special characters
    relative_link = '../output/' + agent.file_path.replace('\\', '/').replace('.md', '')
    relative_link = quote(relative_link, safe='/:')

    # Use description or a fallback
    description = agent.description if agent.description else "No description available"

    # Generate card markdown using HTML/CSS classes for custom styling
    # This will work with Material theme and the custom CSS from phase 3
    card = f"""<div class="agent-card">

**[{agent.title}]({relative_link})**

<span class="agent-category">{category}</span>

{description}

[:material-github: View Repository]({agent.url}){{ .md-button }}

</div>
"""
    return card


def generate_homepage_markdown(agents_by_category: Dict[str, List[AgentMetadata]]) -> str:
    """
    Generate the complete homepage markdown with agent cards organized by category.

    Args:
        agents_by_category: Dictionary mapping category names to lists of AgentMetadata

    Returns:
        Complete markdown string for the homepage
    """
    logger = logging.getLogger(__name__)

    # Calculate statistics
    total_agents = sum(len(agents) for agents in agents_by_category.values())
    total_categories = len(agents_by_category)

    # Generate header section
    markdown = f"""# Welcome to LLM Agents Search

Explore our curated collection of **{total_agents}+ LLM agents and tools** across **{total_categories} categories**.

## Featured Agents

Discover the most popular and innovative LLM agents, frameworks, and tools.

"""

    # Generate category sections with agent cards
    for category_name in sorted(agents_by_category.keys()):
        agents = agents_by_category[category_name]
        logger.debug(f"Generating category section: {category_name} ({len(agents)} agents)")

        # Sort agents alphabetically by title
        sorted_agents = sorted(agents, key=lambda a: a.title.lower())

        markdown += f"### {category_name}\n\n"
        markdown += f"<div class=\"agent-card-grid\">\n\n"

        # Generate cards for each agent
        for agent in sorted_agents:
            card = generate_agent_card(agent, category_name)
            markdown += f"{card}\n"

        markdown += f"</div>\n\n"
        markdown += "---\n\n"

    # Add footer section
    markdown += """## Documentation Structure

The documentation is organized into the following categories:

"""

    # Add category overview (without links)
    for category_name in sorted(agents_by_category.keys()):
        agents = agents_by_category[category_name]
        markdown += f"- **{category_name}** - {len(agents)} agent{'s' if len(agents) != 1 else ''}\n"

    markdown += """
## Getting Started

Browse the agent cards above or use the search to find specific agents. Each agent page includes:
- Detailed description
- GitHub repository link
- Installation instructions
- Usage examples
- Documentation

## Contributing

Found an interesting LLM agent or tool? Consider contributing to our collection!
"""

    return markdown


def write_homepage(markdown_content: str, output_path: str) -> None:
    """
    Write the generated homepage markdown to a file.

    Args:
        markdown_content: Generated markdown content
        output_path: Path where the homepage file should be written

    Raises:
        OSError: If file writing fails
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Writing homepage to: {output_path}")

    try:
        # Create parent directories if they don't exist
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logger.info(f"Successfully wrote homepage: {output_path}")

    except OSError as e:
        logger.error(f"Failed to write homepage {output_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error writing homepage {output_path}: {e}")
        raise


def print_generation_summary(agents_by_category: Dict[str, List[AgentMetadata]]) -> None:
    """
    Print a formatted summary of the homepage generation.

    Args:
        agents_by_category: Dictionary mapping category names to lists of AgentMetadata
    """
    logger = logging.getLogger(__name__)

    # Calculate statistics
    total_agents = sum(len(agents) for agents in agents_by_category.values())
    total_categories = len(agents_by_category)

    # Print overall summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("HOMEPAGE GENERATION SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Generated homepage for {total_agents} agents across {total_categories} categories")
    logger.info("")

    # Print per-category breakdown
    for category_name in sorted(agents_by_category.keys()):
        agents = agents_by_category[category_name]
        logger.info(f"  {category_name}: {len(agents)} agent cards")

    logger.info("")
    logger.info("=" * 70)


def main() -> int:
    """
    Main entry point for the script.

    Gathers agent metadata, generates homepage markdown with card grid,
    and writes to output file.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse command-line arguments
    args = parse_arguments()

    # Set up logging
    log_level = "DEBUG" if args.debug else "INFO"
    logger = setup_logging(log_level)
    logger.info("Starting Homepage Generator")

    # Log configuration
    logger.debug(f"Output directory: {args.output_dir}")
    logger.debug(f"Output file: {args.output}")
    logger.debug(f"Dry run: {args.dry_run}")

    try:
        # Gather agent metadata from markdown files
        agents_by_category = gather_agent_metadata(args.output_dir)

        # Generate homepage markdown
        logger.info("Generating homepage markdown with agent cards")
        markdown_content = generate_homepage_markdown(agents_by_category)

        # Print summary
        print_generation_summary(agents_by_category)

        # Write to file (unless in dry-run mode)
        if not args.dry_run:
            write_homepage(markdown_content, args.output)
        else:
            logger.info(f"[DRY-RUN] Would write homepage to: {args.output}")
            # Print preview of generated markdown
            logger.info("")
            logger.info("=" * 70)
            logger.info("GENERATED MARKDOWN PREVIEW (First 50 lines):")
            logger.info("=" * 70)
            preview_lines = markdown_content.split('\n')[:50]
            for line in preview_lines:
                logger.info(line)
            if len(markdown_content.split('\n')) > 50:
                logger.info("... (truncated)")
            logger.info("=" * 70)

        if args.dry_run:
            logger.info("Dry run mode - no files were written")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Directory not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"No valid data: {e}")
        return 1
    except Exception as e:
        logger.error(f"Script failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
