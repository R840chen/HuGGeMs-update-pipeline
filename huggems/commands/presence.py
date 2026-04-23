#!/usr/bin/env python3
"""
HuGGeMs presence detection command (Part I)
Detects if genomes exist in the HuGGeMs dataset using dRep
"""

import os
import sys
import shutil
import subprocess
import click
import pandas as pd
from pathlib import Path

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
REQUIRED_TOOLS = ["dRep"]
OPTIONAL_TOOLS = ["mash", "nucmer", "fastANI", "mummer"]


# ---------- utilities ----------
def find_genome_files(root, ext):
    """Find genome files with given extension."""
    ext = ext.lower().lstrip('.')
    matches = []
    for p in Path(root).rglob(f'*.{ext}'):
        if p.is_file():
            matches.append(p)
    return matches


def copy_new_files(new_dir, input_dir, suffix):
    """Copy genome files from new_dir into input_dir, renaming to .fna."""
    new_dir = Path(new_dir)
    input_dir = Path(input_dir)
    candidates = find_genome_files(new_dir, suffix)
    
    if not candidates:
        raise SystemExit(f"No files with extension .{suffix} found under {new_dir}")

    copied = []
    dest_map = {}

    for src in candidates:
        dest_name = src.stem + '.fna'
        dest_path = input_dir.joinpath(dest_name)
        i = 1
        while dest_path.exists():
            dest_path = input_dir.joinpath(f'{src.stem}_copy{i}.fna')
            i += 1
        shutil.copy2(src, dest_path)
        dest_path = dest_path.resolve()
        copied.append(dest_path)
        dest_map[dest_path.name] = dest_path

    return copied, dest_map


def write_genome_list(input_dir, genome_list_path):
    """Write a list of all .fna files to genome_list_path."""
    all_fna = find_genome_files(input_dir, 'fna')
    if not all_fna:
        raise SystemExit(f'Error: no .fna files found under {input_dir}')
    
    with open(genome_list_path, 'w') as fh:
        for p in sorted(all_fna):
            fh.write(str(p) + '\n')
    
    return len(all_fna)


def cleanup_copied_files(dest_map, verbose=False):
    """Remove files that were copied from --new-dir into --input-dir."""
    results = []
    for fname, abs_path in dest_map.items():
        try:
            if abs_path.exists():
                abs_path.unlink()
                results.append((abs_path, True))
                if verbose:
                    print(f"  [CLEANUP] Removed: {abs_path}")
            else:
                results.append((abs_path, False))
        except Exception as exc:
            results.append((abs_path, False))
            print(f"  [CLEANUP] Failed to remove {abs_path}: {exc}", file=sys.stderr)
    return results


def run_drep(output_dir, genome_list_path, threads, ani_threshold=95.0):
    """Run dRep compare."""
    drep_cmd = [
        'dRep', 'compare', str(output_dir),
        '-p', str(threads),
        '-g', str(genome_list_path),
        '-pa', str(ani_threshold / 100),  # Convert percentage to fraction
        '--multiround_primary_clustering',
        '--primary_chunksize', '3000',
        '-d',
        '-nc', '0.6',
    ]
    print('Constructed dRep command:')
    print(' '.join(drep_cmd))
    
    try:
        proc = subprocess.run(drep_cmd, check=False)
        return proc.returncode
    except FileNotFoundError:
        print('Error: dRep executable not found in PATH.', file=sys.stderr)
        return 127


def find_cdb_file(drep_out):
    """Find Cdb.csv or CdbF.csv in dRep output."""
    dt_dir = Path(drep_out) / 'data_tables'
    candidates = [dt_dir / 'Cdb.csv', dt_dir / 'CdbF.csv']
    for c in candidates:
        if c.exists():
            return c
    return None


def match_genome_entry(genome_entry, file_path):
    """Match genome entry to file path."""
    g = genome_entry.strip()
    if g == file_path.name:
        return True
    if g.endswith(file_path.name):
        return True
    if g == file_path.stem or g.endswith(file_path.stem):
        return True
    for ext in ('fna', 'fasta'):
        if g.endswith(f"{file_path.stem}.{ext}"):
            return True
    if file_path.stem in g:
        return True
    return False


def extract_unique_newgenomes(drep_out, new_dir, input_dir, unique_dest, verbose=False):
    """Extract new genomes that occupy unique primary clusters."""
    cdb = find_cdb_file(drep_out)
    if cdb is None:
        raise SystemExit(f"Error: could not find Cdb.csv in {drep_out}/data_tables")

    df = pd.read_csv(cdb, dtype=str, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    
    cluster_map = {}
    for _, row in df.iterrows():
        pc = str(row['primary_cluster']).strip()
        g = str(row['genome']).strip()
        cluster_map.setdefault(pc, []).append(g)

    genome_to_cluster = {}
    for pc, members in cluster_map.items():
        for g in members:
            genome_to_cluster.setdefault(g, []).append(pc)

    new_files = sorted([
        p for p in Path(new_dir).rglob('*')
        if p.is_file() and p.suffix.lower() in ('.fna', '.fasta')
    ])

    cdb_genomes = list(genome_to_cluster.keys())
    unique_copied = []

    for newf in new_files:
        matched_entries = [g for g in cdb_genomes if match_genome_entry(g, newf)]
        if not matched_entries:
            continue

        unique_for_this_file = False
        for g_entry in matched_entries:
            clusters = genome_to_cluster.get(g_entry, [])
            for pc in clusters:
                members = cluster_map.get(pc, [])
                members_count = len(members)
                member_is_from_newdir = [
                    any(match_genome_entry(m, nf) for nf in new_files)
                    for m in members
                ]
                all_members_from_newdir = all(member_is_from_newdir)
                if members_count == 1 or all_members_from_newdir:
                    unique_for_this_file = True
                    if verbose:
                        print(f"[UNIQUE] {newf.name} -> cluster {pc}")
                    break
            if unique_for_this_file:
                break

        if not unique_for_this_file:
            continue

        # Find source file
        candidate_src = None
        p_in_input = input_dir / newf.name
        if p_in_input.exists():
            candidate_src = p_in_input
        else:
            matches_in_input = list(Path(input_dir).rglob(f"{newf.stem}*"))
            if matches_in_input:
                for m in matches_in_input:
                    if m.suffix.lower() == '.fna':
                        candidate_src = m
                        break
                candidate_src = candidate_src or matches_in_input[0]

        if candidate_src is None:
            candidate_src = newf

        dest = Path(unique_dest).resolve()
        dest.mkdir(parents=True, exist_ok=True)
        dest_path = dest / candidate_src.name
        shutil.copy2(candidate_src, dest_path)
        unique_copied.append((candidate_src, dest_path))
        if verbose:
            print(f"Copied: {candidate_src} -> {dest_path}")

    return unique_copied


@click.command()
@click.option('--new-dir', required=True, type=click.Path(exists=True),
              help='Directory containing new genome files to check')
@click.option('--input-dir', required=True, type=click.Path(exists=True),
              help='Main genomes directory (HuGGeMs representative genomes)')
@click.option('--output-dir', required=True, type=click.Path(),
              help='Output directory for dRep results')
@click.option('--suffix', default='fna', type=click.Choice(['fna', 'fasta']),
              help='Suffix of new genome files (default: fna)')
@click.option('--threads', default=64, type=int,
              help='Number of threads for dRep (default: 64)')
@click.option('--ani-threshold', default=95.0, type=float,
              help='ANI threshold for considering genomes as same species (default: 95.0)')
@click.option('--genome-list', type=click.Path(),
              help='Path to genome list file (default: <input-dir>/genome_list.txt)')
@click.option('--dry-run', is_flag=True,
              help='If set, do not run dRep; only copy files and write genome list')
@click.option('--extract-unique', is_flag=True,
              help='After dRep, extract new genomes that occupy unique primary clusters')
@click.option('--unique-dest', type=click.Path(),
              help='Where to copy unique new genomes (default: <input-dir>/unique-new-genomes)')
@click.option('--unique-list', type=click.Path(),
              help='Path to write unique genome list (default: <unique-dest>/unique_genomes.txt)')
@click.option('--cleanup-copied', is_flag=True,
              help='After pipeline finishes, remove files copied from --new-dir out of --input-dir')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
def presence(new_dir, input_dir, output_dir, suffix, threads, ani_threshold,
             genome_list, dry_run, extract_unique, unique_dest, unique_list,
             cleanup_copied, verbose):
    """Part I - Detect if genomes exist in HuGGeMs dataset
    
    Compares query genomes against HuGGeMs representative genomes
    to determine if they are already represented in the database.
    
    Example:
        huggems presence --new-dir ./query_genomes/ --input-dir ./HuGGeMs_representatives/ --output-dir ./results/ --threads 64 --extract-unique --cleanup-copied
    """
    setup_logging(verbose=verbose)
    log_step("Part I: Presence Detection", "Using dRep pipeline")
    
    input_dir = Path(input_dir).expanduser().resolve()
    new_dir = Path(new_dir).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check tool availability
    log_step("Checking dependencies", "")
    tool_status = check_tools_available(REQUIRED_TOOLS)
    
    if not tool_status.get('dRep', False):
        log_warning("Missing required tool: dRep")
        log_warning("Please install: conda install -c bioconda drep")
        sys.exit(1)
    
    # Determine genome list path
    genome_list_path = (
        Path(genome_list).expanduser().resolve()
        if genome_list
        else input_dir / 'genome_list.txt'
    )
    
    # Step 1: Copy new genomes into input-dir
    log_step("Copying new genomes", "")
    suffix = suffix.lower().lstrip('.')
    copied_files, dest_map = copy_new_files(new_dir, input_dir, suffix)
    print(f'Copied {len(copied_files)} files into {input_dir} (converted to .fna)')
    
    if verbose:
        for p in copied_files:
            print(f'  copied: {p}')
    
    # Step 2: Write genome list
    log_step("Writing genome list", "")
    total = write_genome_list(input_dir, genome_list_path)
    print(f'Wrote genome list to {genome_list_path} with {total} entries')
    
    if dry_run:
        print('Dry run requested; exiting before running dRep')
        sys.exit(0)
    
    # Step 3: Run dRep
    log_step("Running dRep compare", "")
    rc = run_drep(output_dir, genome_list_path, threads, ani_threshold)
    if rc != 0:
        print(f'dRep exited with return code {rc}', file=sys.stderr)
        sys.exit(rc)
    
    # Step 4: Extract unique genomes
    if extract_unique:
        log_step("Extracting unique genomes", "")
        u_dest = (
            Path(unique_dest)
            if unique_dest
            else input_dir / 'unique-new-genomes'
        )
        unique = extract_unique_newgenomes(
            output_dir, new_dir, input_dir, u_dest, verbose=verbose
        )
        print(f'Extracted {len(unique)} unique genomes')
        
        u_list_path = (
            Path(unique_list).expanduser().resolve()
            if unique_list
            else u_dest / 'unique_genomes.txt'
        )
        with open(u_list_path, 'w') as fh:
            for _, dest_path in unique:
                fh.write(str(dest_path) + '\n')
        print(f'Unique genome list written to: {u_list_path}')
    
    # Step 5: Cleanup
    if cleanup_copied:
        log_step("Cleaning up copied files", "")
        cleanup_results = cleanup_copied_files(dest_map, verbose=verbose)
        success_count = sum(1 for _, ok in cleanup_results if ok)
        print(f'Cleanup done: {success_count} removed, {len(cleanup_results) - success_count} failed/skipped')
    
    log_success("Part I completed!")
    print(f'\nResults directory: {output_dir}')
