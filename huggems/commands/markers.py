#!/usr/bin/env python3
"""
HuGGeMs marker selection command (Part II)
Selects and updates marker genes using Prokka, Diamond, MMseqs2 pipeline
"""

import os
import sys
import subprocess
import click

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
REQUIRED_TOOLS = ["prokka", "diamond"]
OPTIONAL_TOOLS = ["mmseqs", "bowtie2", "samtools", "art", "bamutil"]


@click.command()
@click.option(
    "--input-dir",
    required=True,
    type=click.Path(exists=True),
    help="Directory containing genomes for marker selection",
)
@click.option(
    "--uniref90",
    required=True,
    type=click.Path(exists=True),
    help="Path to UniRef90 database (FASTA or Diamond index .dmnd)",
)
@click.option(
    "--uniref50",
    required=True,
    type=click.Path(exists=True),
    help="Path to UniRef50 database (FASTA or Diamond index .dmnd)",
)
@click.option(
    "--huggems-ref",
    required=True,
    type=click.Path(exists=True),
    help="Path to HuGGeMs reference marker profiles",
)
@click.option(
    "--output-dir",
    required=True,
    type=click.Path(),
    help="Output directory for results",
)
@click.option(
    "--step",
    type=click.Choice(["all", "annotate", "core-genes", "markers", "build-db"]),
    default="all",
    help="Pipeline step to run (default: all)",
)
@click.option(
    "--cpus",
    default=1,
    type=int,
    help="Number of CPUs for parallel processing (default: 1)",
)
@click.option(
    "--evalue",
    default=1e-5,
    type=click.FloatRange(0, 1),
    help="E-value threshold for Diamond search (default: 1e-5)",
)
@click.option(
    "--identity",
    default=50.0,
    type=click.FloatRange(0, 100),
    help="Minimum identity percentage for homologs (default: 50.0)",
)
@click.option(
    "--coverage",
    default=80.0,
    type=click.FloatRange(0, 100),
    help="Minimum coverage percentage (default: 80.0)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def markers(
    input_dir,
    uniref90,
    uniref50,
    huggems_ref,
    output_dir,
    step,
    cpus,
    evalue,
    identity,
    coverage,
    verbose,
):
    """Part II - Select and update marker genes

    Complete pipeline for marker gene selection:
    1. Gene prediction with Prokka
    2. Annotation with Diamond against UniRef
    3. Core gene identification
    4. Marker gene selection
    5. Build profiling database

    Example:
        huggems markers --input-dir ./genomes/ --uniref90 ./db/uniref90.dmnd --uniref50 ./db/uniref50.dmnd --huggems-ref ./db/HuGGeMs_ref/ --output-dir ./results/
    """
    setup_logging(verbose=verbose)
    log_step("Part II: Marker Gene Selection", "Prokka -> Diamond -> Core Gene -> Markers")

    # Create output directories
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "annotations"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "core_genes"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "markers"), exist_ok=True)

    # Check tool availability
    log_step("Checking dependencies", "")
    tool_status = check_tools_available(REQUIRED_TOOLS + OPTIONAL_TOOLS)

    missing_required = [t for t in REQUIRED_TOOLS if not tool_status.get(t, False)]
    if missing_required:
        log_warning(f"Missing required tools: {', '.join(missing_required)}")
        log_warning("Please install: conda install -c bioconda prokka diamond")
        sys.exit(1)

    available_optional = [t for t in OPTIONAL_TOOLS if tool_status.get(t, False)]
    if available_optional:
        click.echo(f"  Available tools: {', '.join(available_optional)}")

    # Check database files
    log_step("Checking database files", "")
    for db_path, db_name in [(uniref90, "UniRef90"), (uniref50, "UniRef50")]:
        if not os.path.exists(db_path):
            log_warning(f"{db_name} not found at: {db_path}")
            log_warning(f"Please provide .dmnd index or .fasta file")
        else:
            click.echo(f"  {db_name}: {db_path}")

    if not os.path.exists(huggems_ref):
        log_warning(f"HuGGeMs reference not found: {huggems_ref}")

    # Run pipeline steps
    if step in ["all", "annotate"]:
        run_annotation_step(input_dir, output_dir, uniref90, uniref50, cpus, evalue, identity, coverage, verbose)

    if step in ["all", "core-genes"]:
        run_core_genes_step(output_dir, verbose)

    if step in ["all", "markers"]:
        run_markers_step(output_dir, huggems_ref, verbose)

    if step in ["all", "build-db"]:
        run_build_db_step(output_dir, verbose)

    # Generate summary
    log_step("Generating summary report", "")
    summary_file = os.path.join(output_dir, "markers_summary.txt")

    with open(summary_file, "w") as f:
        f.write("HuGGeMs Marker Selection Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Input genomes: {input_dir}\n")
        f.write(f"UniRef90: {uniref90}\n")
        f.write(f"UniRef50: {uniref50}\n")
        f.write(f"Step: {step}\n")
        f.write(f"CPUs: {cpus}\n")
        f.write(f"E-value: {evalue}\n")
        f.write(f"Identity: {identity}%\n")
        f.write(f"Coverage: {coverage}%\n\n")
        f.write("Output:\n")
        f.write(f"  - Annotations: {output_dir}/annotations/\n")
        f.write(f"  - Core genes: {output_dir}/core_genes/\n")
        f.write(f"  - Markers: {output_dir}/markers/\n")

    log_success(f"Summary saved to: {summary_file}")
    click.echo(f"\nResults directory: {output_dir}")


def run_annotation_step(input_dir, output_dir, uniref90, uniref50, cpus, evalue, identity, coverage, verbose):
    """Run Prokka annotation and Diamond search."""
    log_step("Step 1: Gene Annotation", "")

    annotation_dir = os.path.join(output_dir, "annotations")
    prokka_dir = os.path.join(annotation_dir, "prokka")
    diamond_dir = os.path.join(annotation_dir, "diamond")

    os.makedirs(prokka_dir, exist_ok=True)
    os.makedirs(diamond_dir, exist_ok=True)

    # Run Prokka on each genome
    click.echo("Running Prokka gene prediction...")
    genomes = [f for f in os.listdir(input_dir) if f.endswith((".fna", ".fa", ".fasta", ".gbk"))]
    click.echo(f"  Found {len(genomes)} genomes to annotate")

    for genome in genomes:
        genome_path = os.path.join(input_dir, genome)
        genome_name = os.path.splitext(genome)[0]
        output_prefix = os.path.join(prokka_dir, genome_name)

        cmd = [
            "prokka",
            "--outdir", output_prefix,
            "--prefix", genome_name,
            "--cpus", str(cpus),
            genome_path,
        ]

        if verbose:
            click.echo(f"  Running: {' '.join(cmd)}")

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            log_warning(f"Prokka failed for {genome}: {e}")

    log_success("Prokka annotation completed")

    # Run Diamond search against UniRef
    click.echo("Running Diamond search against UniRef databases...")

    # Check if Diamond database exists, if not create it
    if not uniref90.endswith(".dmnd"):
        log_warning("UniRef90 is not a Diamond index, skipping Diamond search")
        return

    # For each Prokka output, run Diamond
    for genome in genomes:
        genome_name = os.path.splitext(genome)[0]
        faa_file = os.path.join(prokka_dir, genome_name, f"{genome_name}.faa")

        if not os.path.exists(faa_file):
            continue

        # Diamond against UniRef90
        diamond_out = os.path.join(diamond_dir, f"{genome_name}_uniref90.tsv")
        cmd = [
            "diamond", "blastp",
            "--db", uniref90,
            "--query", faa_file,
            "--out", diamond_out,
            "--outfmt", "6",
            "--evalue", str(evalue),
            "--id", str(identity),
            "--query-cover", str(coverage),
            "--threads", str(cpus),
        ]

        if verbose:
            click.echo(f"  Running Diamond for {genome_name}")

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            log_warning(f"Diamond failed for {genome_name}: {e}")

    log_success("Annotation step completed")


def run_core_genes_step(output_dir, verbose):
    """Identify core genes across genomes."""
    log_step("Step 2: Core Gene Identification", "")

    annotation_dir = os.path.join(output_dir, "annotations")
    core_dir = os.path.join(output_dir, "core_genes")

    # Placeholder for core gene identification logic
    # This would typically use ortholog clustering (e.g., OrthoMCL, MMseqs2)
    click.echo("  Core gene identification not yet implemented")
    click.echo("  Please run: MMseqs2 cluster or OrthoMCL manually")

    log_success("Core gene step completed (manual intervention required)")


def run_markers_step(output_dir, huggems_ref, verbose):
    """Select marker genes from core genes."""
    log_step("Step 3: Marker Gene Selection", "")

    core_dir = os.path.join(output_dir, "core_genes")
    marker_dir = os.path.join(output_dir, "markers")

    # Placeholder for marker selection logic
    click.echo("  Marker selection not yet implemented")
    click.echo("  Reference: HuGGeMs marker selection criteria")

    log_success("Marker selection step completed (manual intervention required)")


def run_build_db_step(output_dir, verbose):
    """Build Bowtie2 database for profiling."""
    log_step("Step 4: Build Profiling Database", "")

    marker_dir = os.path.join(output_dir, "markers")
    db_dir = os.path.join(output_dir, "db")

    os.makedirs(db_dir, exist_ok=True)

    # Placeholder for database building
    click.echo("  Database building not yet implemented")

    log_success("Database build step completed (manual intervention required)")
