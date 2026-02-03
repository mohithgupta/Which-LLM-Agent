#!/usr/bin/env python3
"""
Agent Metadata Gatherer

This script scans the output/ directory and extracts agent metadata from
markdown frontmatter. It gathers all agent information including title,
description, category, and URL for use in generating the homepage.

Output is structured data suitable for homepage card grid generation.
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
        description="Gather agent metadata from markdown files in output/ directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default settings
  %(prog)s

  # Specify custom output directory
  %(prog)s --output-dir custom_output

  # Output to JSON file
  %(prog)s --json-output agents.json

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
        "--json-output",
        type=str,
        default=None,
        help="Optional JSON output file path for gathered metadata"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and gather but don't write output files"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging for troubleshooting"
    )

    args = parser.parse_args()
    logger.debug(
        f"Arguments parsed: output_dir={args.output_dir}, "
        f"json_output={args.json_output}, dry_run={args.dry_run}, "
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


def print_agent_summary(agents_by_category: Dict[str, List[AgentMetadata]]) -> None:
    """
    Print a formatted summary of gathered agent metadata.

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
    logger.info("AGENT METADATA SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Found {total_agents} agents across {total_categories} categories")
    logger.info("")

    # Print per-category breakdown
    for category_name in sorted(agents_by_category.keys()):
        agents = agents_by_category[category_name]
        logger.info(f"  {category_name}: {len(agents)} agents")

        # Print details for each agent in the category
        for agent in agents:
            desc_preview = ""
            if agent.description:
                desc_preview = f" - {agent.description[:60]}{'...' if len(agent.description) > 60 else ''}"
            logger.info(f"    - {agent.title}{desc_preview}")

    logger.info("")
    logger.info("=" * 70)


def write_json_output(
    agents_by_category: Dict[str, List[AgentMetadata]],
    output_path: str
) -> None:
    """
    Write gathered agent metadata to a JSON file.

    Args:
        agents_by_category: Dictionary mapping category names to lists of AgentMetadata
        output_path: Path where the JSON file should be written

    Raises:
        OSError: If file writing fails
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Writing JSON output to: {output_path}")

    try:
        # Convert dataclasses to dicts for JSON serialization
        output_data = {
            category: [asdict(agent) for agent in agents]
            for category, agents in agents_by_category.items()
        }

        # Add summary statistics
        total_agents = sum(len(agents) for agents in agents_by_category.values())
        output_data['_summary'] = {
            'total_categories': len(agents_by_category),
            'total_agents': total_agents,
            'categories': list(agents_by_category.keys())
        }

        # Write to JSON file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully wrote JSON file: {output_path}")

    except OSError as e:
        logger.error(f"Failed to write JSON file {output_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error writing JSON file {output_path}: {e}")
        raise


def main() -> int:
    """
    Main entry point for the script.

    Scans the output directory for markdown files, extracts metadata from
    frontmatter, and outputs a summary or JSON file.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse command-line arguments
    args = parse_arguments()

    # Set up logging
    log_level = "DEBUG" if args.debug else "INFO"
    logger = setup_logging(log_level)
    logger.info("Starting Agent Metadata Gatherer")

    # Log configuration
    logger.debug(f"Output directory: {args.output_dir}")
    logger.debug(f"JSON output: {args.json_output}")
    logger.debug(f"Dry run: {args.dry_run}")

    try:
        # Gather agent metadata from markdown files
        agents_by_category = gather_agent_metadata(args.output_dir)

        # Print summary to console
        print_agent_summary(agents_by_category)

        # Write JSON output if requested (and not in dry-run mode)
        if args.json_output and not args.dry_run:
            write_json_output(agents_by_category, args.json_output)
        elif args.json_output and args.dry_run:
            logger.info(f"[DRY-RUN] Would create JSON file: {args.json_output}")

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
