#!/usr/bin/env python3
"""
Hybrid Data Fetcher for awesome-llm-apps

This script fetches project data from the awesome-llm-apps repository using a
three-tier approach:
1. Parse the main README.md to extract the complete project catalog with categories
2. Use GitHub API to fetch individual project READMEs when available
3. Generate metadata from Python files for projects without READMEs

Output is structured data suitable for MkDocs documentation generation.
"""

import argparse
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Project:
    """
    Represents a single project entry from the awesome-llm-apps repository.

    Attributes:
        title: The project name/title
        url: The GitHub repository URL
        description: Optional project description
        category: The category this project belongs to
    """
    title: str
    url: str
    description: Optional[str] = None
    category: str = ""


# Configure logging
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
    return logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the script.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Fetch and process project data from awesome-llm-apps repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default settings
  %(prog)s

  # Specify custom output directory
  %(prog)s --output-dir custom_output

  # Run without caching
  %(prog)s --skip-cache

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
        help="Output directory for generated markdown files (default: output)"
    )

    parser.add_argument(
        "--skip-cache",
        action="store_true",
        help="Skip using cached data and refetch all READMEs"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and process but don't write output files"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging for troubleshooting"
    )

    parser.add_argument(
        "--github-token",
        type=str,
        default=os.environ.get("GITHUB_TOKEN", ""),
        help="GitHub Personal Access Token (default: from GITHUB_TOKEN env var)"
    )

    return parser.parse_args()


def parse_main_readme(readme_path: str) -> Dict[str, List[Project]]:
    """
    Parse the main awesome-llm-apps README.md to extract projects grouped by category.

    This function reads a markdown file and extracts project entries organized by
    category headers. It expects the format:
        ## Category Name
        - [Project Title](URL) - Description

    Args:
        readme_path: Path to the README.md file to parse

    Returns:
        Dictionary mapping category names to lists of Project objects

    Raises:
        FileNotFoundError: If the readme_path does not exist
        ValueError: If the README format is invalid
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Parsing main README: {readme_path}")

    readme_file = Path(readme_path)
    if not readme_file.exists():
        logger.error(f"README file not found: {readme_path}")
        raise FileNotFoundError(f"README file not found: {readme_path}")

    try:
        content = readme_file.read_text(encoding="utf-8")
    except IOError as e:
        logger.error(f"Failed to read README file: {e}")
        raise

    # Dictionary to store categories and their projects
    categories: Dict[str, List[Project]] = {}
    current_category = "Uncategorized"

    # Regex patterns
    category_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    project_pattern = re.compile(
        r"-\s+\[([^\]]+)\]\(([^)]+)\)\s*(?:-\s*(.+))?$",
        re.MULTILINE
    )

    # Split content into lines for processing
    lines = content.split("\n")

    for line in lines:
        # Check if line is a category header
        category_match = category_pattern.match(line.strip())
        if category_match:
            current_category = category_match.group(1).strip()
            logger.debug(f"Found category: {current_category}")
            if current_category not in categories:
                categories[current_category] = []
            continue

        # Check if line is a project entry
        project_match = project_pattern.match(line.strip())
        if project_match:
            title = project_match.group(1).strip()
            url = project_match.group(2).strip()
            description = project_match.group(3).strip() if project_match.group(3) else None

            project = Project(
                title=title,
                url=url,
                description=description,
                category=current_category
            )

            categories.setdefault(current_category, []).append(project)
            logger.debug(f"Added project '{title}' to category '{current_category}'")

    # Summary statistics
    total_projects = sum(len(projects) for projects in categories.values())
    logger.info(f"Parsed {len(categories)} categories with {total_projects} total projects")

    if total_projects == 0:
        logger.warning("No projects found in README - check format")
        raise ValueError("No valid project entries found in README")

    return categories


def main() -> int:
    """
    Main entry point for the script.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse command-line arguments
    args = parse_arguments()

    # Set up logging
    log_level = "DEBUG" if args.debug else "INFO"
    logger = setup_logging(log_level)
    logger.info("Starting Hybrid Data Fetcher for awesome-llm-apps")

    # Log configuration
    logger.debug(f"Output directory: {args.output_dir}")
    logger.debug(f"Skip cache: {args.skip_cache}")
    logger.debug(f"Dry run: {args.dry_run}")
    logger.debug(f"GitHub token provided: {bool(args.github_token)}")

    try:
        # TODO: Implement main fetching logic in subsequent subtasks
        logger.info("Script structure initialized successfully")
        logger.info("Implementation will continue in subsequent subtasks")

        if args.dry_run:
            logger.info("Dry run mode - no files will be written")

        return 0

    except Exception as e:
        logger.error(f"Script failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
