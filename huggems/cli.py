#!/usr/bin/env python3
"""
HuGGeMs CLI - Command-line interface for HuGGeMs update pipelines
"""

import sys
import click

from huggems.commands.presence import presence
from huggems.commands.markers import markers


@click.group()
@click.version_option(version="0.1.0", prog_name="huggems")
def cli():
    """HuGGeMs - Human Gut Microbial Gene Markers Update Tool

    A bioinformatics pipeline for updating HuGGeMs database.

    Commands:
        presence   Part I - Detect if genomes exist in HuGGeMs dataset
        markers    Part II - Select and update marker genes

    Examples:
        huggems presence --help
        huggems markers --help
    """
    pass


# Register subcommands
cli.add_command(presence)
cli.add_command(markers)


if __name__ == "__main__":
    cli()
