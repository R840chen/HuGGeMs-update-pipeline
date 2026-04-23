# HuGGeMs-update Required Datasets

This document provides download information for all datasets required by the HuGGeMs-update pipeline.

---

## 1. HuGGeMs Representative Clusters (11,167 genomes)

**Purpose**: Used by Part I for genome distance comparisons

**Status**: Download links are placeholders in the original README. You need to obtain these from:

### Options:
1. **Original HuGGeMs publication** - Search for the original HuGGeMs paper for data availability section
2. **Contact repository maintainer** - Raise an issue at https://github.com/R840chen/HuGGeMs-update-pipelines
3. **HuGGeMs Data Repository** - Check if there's an official data hosting site (e.g., figshare, zenodo, or institutional repository)

**Expected format**: Collection of genome files (.fna, .fa, or .gbk)
**Typical naming**: Files may be organized by cluster ID (e.g., `cluster_001.fna`, `cluster_002.fna`)

---

## 2. HuGGeMs Dataset (Marker Profiles / Reference)

**Purpose**: Used for metagenome profiling and marker set updates (Part II)

**Same source as above** - Contact the repository maintainer or check the original publication.

---

## 3. UniRef90 Database

**Purpose**: Used by Part II for protein annotation

### Official Download Sources:

#### Option 1: UniProt FTP Server (Recommended)
```bash
# FTP access
ftp://ftp.uniprot.org/pub/databases/uniprot/uniref/uniref90/

# HTTP download (direct links)
wget https://ftp.uniprot.org/pub/databases/uniprot/uniref/uniref90/uniref90.fasta.gz

# Or use rsync for reliable transfer
rsync -avz rsync://ftp.uniprot.org:/pub/databases/uniprot/uniref/uniref90/ ./uniref90/
```

#### Option 2: EBI Mirror (Faster for Asia users)
```bash
# EBI ENA mirror
wget https://ftp.ebi.ac.uk/pub/databases/uniprot/uniref/uniref90/uniref90.fasta.gz

# Use Aspera for large files (if available)
ascp -i ~/.aspera/connect/etc/asperaweb_id_dsa.openssh \
     -k 1 -T -l 2000m \
     anonftp@ftp-private.ncbi.nlm.nih.gov:/databases/uniprot/releases/./uniref90.*/uniref90.fasta.gz .
```

#### Option 3: NCBI BLAST Database
```bash
# Download via update_blastdb.pl
update_blastdb.pl --decompress uniref90
```

### File Information:
| Property | Value |
|----------|-------|
| Format | FASTA (.fasta.gz) |
| Typical size | ~25 GB (compressed) |
| Version | Check UniProt for current release |
| Cluster threshold | 90% sequence identity |

---

## 4. UniRef50 Database

**Purpose**: Used by Part II for protein annotation (more compact version)

### Official Download Sources:

#### Option 1: UniProt FTP Server
```bash
# FTP access
ftp://ftp.uniprot.org/pub/databases/uniprot/uniref/uniref50/

# HTTP download
wget https://ftp.uniprot.org/pub/databases/uniprot/uniref/uniref50/uniref50.fasta.gz
```

#### Option 2: EBI Mirror
```bash
wget https://ftp.ebi.ac.uk/pub/databases/uniprot/uniref/uniref50/uniref50.fasta.gz
```

### File Information:
| Property | Value |
|----------|-------|
| Format | FASTA (.fasta.gz) |
| Typical size | ~13 GB (compressed) |
| Version | Check UniProt for current release |
| Cluster threshold | 50% sequence identity |

---

## 5. Diamond Database Format Conversion

After downloading UniRef, convert to Diamond format for faster searching:

```bash
# Activate environment
conda activate huggems-update

# Create Diamond database from UniRef90
diamond makedb --in uniref90.fasta.gz -d uniref90.dmnd

# Create Diamond database from UniRef50
diamond makedb --in uniref50.fasta.gz -d uniref50.dmnd
```

---

## 6. Summary Table

| Dataset | Size (compressed) | Source | Download Command |
|---------|-------------------|--------|------------------|
| HuGGeMs Representatives | Varies (typically 50-100 GB) | Contact maintainer | N/A |
| UniRef90 | ~25 GB | UniProt/EBI/NCBI | `wget https://ftp.ebi.ac.uk/pub/databases/uniprot/uniref/uniref90/uniref90.fasta.gz` |
| UniRef50 | ~13 GB | UniProt/EBI/NCBI | `wget https://ftp.ebi.ac.uk/pub/databases/uniprot/uniref/uniref50/uniref50.fasta.gz` |

---

## 7. Storage Requirements

| Component | Estimated Size |
|-----------|----------------|
| UniRef90 (FASTA + Diamond DB) | ~50 GB |
| UniRef50 (FASTA + Diamond DB) | ~25 GB |
| HuGGeMs Genomes | ~50-100 GB |
| Temporary working space | 100+ GB |
| **Total Required** | **250-300 GB** |

---

## 8. Verification Commands

```bash
# Check downloaded files
ls -lh uniref90.fasta.gz uniref50.fasta.gz

# Verify file integrity
md5sum uniref90.fasta.gz
md5sum uniref50.fasta.gz

# Check sequence count in UniRef90
zcat uniref90.fasta.gz | grep "^>" | wc -l
```

---

## Notes

1. **Download speed**: EBI mirror (https://ftp.ebi.ac.uk) is often faster for Asian users
2. **Resume downloads**: Use `wget -c` or `curl -C -` to resume interrupted downloads
3. **Disk space**: Ensure sufficient space before downloading; UniRef databases are large
4. **Alternative databases**: If UniRef is too large, consider using UniRef50 only for initial testing
