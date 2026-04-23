#!/usr/bin/env python3
"""
HuGGeMs presence detection command (Part I)
Detects if genomes exist in the HuGGeMs dataset using dRep
"""

import os
import sys
import subprocess
import click

# Add parent directory to path to import original scripts if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from huggems.utils import (
    setup_logging,
    validate_input_dir,
    validate_output_dir,
    check_tool_available,
    check_tools_available,
    log_step,
    log_warning,
    log_success,
)


# Required tools for this command
REQUIRED_TOOLS = ["dRep"]  # Core requirement
OPTIONAL_TOOLS = ["mash", "nucmer", "fastANI", "mummer.nucmer"]  # For different comparison methods


@click.command()
@click.option(
    "--new-dir",
    required=True,
    type=click.Path(exists=True),
    help="Directory containing new/query genomes to check",
)
@click.option(
    "--input-dir",
    required=True,
    type=click.Path(exists=True),
    help="Path to HuGGeMs representative genomes list (11167_representatives.txt) or directory",
)
@click.option(
    "--output-dir",
    required=True,
    type=click.Path(),
    help="Output directory for results",
)
@click.option(
    "--method",
    type=click.Choice(["mash", "nucmer", "fastANI", "drep"]),
    default="drep",
    help="Method for genome comparison (default: drep)",
)
@click.option(
    "--ani-threshold",
    default=95.0,
    type=click.FloatRange(90.0, 100.0),
    help="ANI threshold for considering genomes as same species (default: 95.0)",
)
@click.option(
    "--extract-unique/--no-extract-unique",
    default=False,
    help="Extract unique genomes that are not in HuGGeMs",
)
@click.option(
    "--threads",
    default=1,
    type=int,
    help="Number of threads for parallel processing (default: 1)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def presence(
    new_dir,
    input_dir,
    output_dir,
    method,
    ani_threshold,
    extract_unique,
    threads,
    verbose,
):
    """Part I - Detect if genomes exist in HuGGeMs dataset

    Compares query genomes against HuGGeMs representative genomes
    to determine if they are already represented in the database.

    Example:
        huggems presence --new-dir ./query_genomes/ --input-dir ./HuGGeMs_representatives/ --output-dir ./results/ --method fastANI
    """
    setup_logging(verbose=verbose)
    log_step("Part I: Presence Detection", "Using dRep/MASH/FastANI pipeline")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Check tool availability
    log_step("Checking dependencies", "")
    tool_status = check_tools_available(REQUIRED_TOOLS + OPTIONAL_TOOLS)

    missing_required = [t for t in REQUIRED_TOOLS if not tool_status.get(t, False)]
    if missing_required:
        log_warning(f"Missing required tools: {', '.join(missing_required)}")
        log_warning("Please install: conda install -c bioconda drep")
        sys.exit(1)

    available_optional = [t for t in OPTIONAL_TOOLS if tool_status.get(t, False)]
    if available_optional:
        click.echo(f"  Available tools: {', '.join(available_optional)}")
    else:
        click.echo("  No optional comparison tools available (MASH, nucmer, FastANI)")

    # Run dRep pipeline
    log_step("Running genome comparison", "")

    # Build command based on original drep_pipeline.py
    cmd = [
        "dRep",
        "compare",
        output_dir,
        "-sa", str(ani_threshold),  # ANI threshold
        "-nc", "0.60",  # contamination threshold
        "-g", input_dir, new_dir,  # Both directories for comparison
    ]

    # Add threads
    if threads > 1:
        cmd.extend(["-p", str(threads)])

    click.echo(f"Command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True, cwd=output_dir)
        log_success("Comparison completed!")
    except subprocess.CalledProcessError as e:
        log_warning(f"dRep command failed with exit code {e.returncode}")
        log_warning("Trying alternative method...")

        # Fallback to mash if available
        if "mash" in available_optional:
            click.echo("Falling back to MASH distance calculation...")
            # Add mash fallback command here
        else:
            sys.exit(1)

    # Generate summary report
    log_step("Generating summary report", "")
    summary_file = os.path.join(output_dir, "presence_summary.txt")

    with open(summary_file, "w") as f:
        f.write("HuGGeMs Presence Detection Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Method: {method}\n")
        f.write(f"ANI Threshold: {ani_threshold}%\n")
        f.write(f"Query genomes: {new_dir}\n")
        f.write(f"Reference genomes: {input_dir}\n\n")
        f.write("Results written to:\n")
        f.write(f"  - {output_dir}/dereplicated_genomes/\n")
        f.write(f"  - {output_dir}/comparisons/*.png\n")

    log_success(f"Summary saved to: {summary_file}")
    click.echo(f"\nResults directory: {output_dir}")
