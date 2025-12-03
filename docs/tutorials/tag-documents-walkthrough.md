# Tag Documents Workflow Walkthrough

**Time: 10 minutes**

This tutorial walks you through running a complete real-world workflow that demonstrates cyberian's key features: preconditions, auto-sync, validation, and error handling.

## Prerequisites

- Completed [Getting Started](getting-started.md)
- Python 3.10+ installed (for validation script)

## What You'll Build

A workflow that:

1. **Tags biomedical abstracts** with controlled vocabulary keywords
2. **Validates** the results using an external Python script
3. **Retries** automatically if validation fails
4. **Auto-syncs** configuration files to your workspace

This demonstrates **workflow-level validation** with the "determinism sandwich" pattern:

```
┌─────────────────────────────────────┐
│  Outer Loop (cyberian)              │  ← Deterministic orchestration
│  • Workflow definition              │
│  • Success criteria validation      │
│  • Retry logic                      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Middle Layer (AI Agent)            │  ← Non-deterministic reasoning
│  • Reads abstracts                  │
│  • Decides which tags fit           │
│  • Creates tags.json                │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Bottom Layer (Tools/Validation)    │  ← Deterministic operations
│  • File I/O (read, write)           │
│  • Validation script checks         │
│  • Per-file constraint checks       │
└─────────────────────────────────────┘
```

The key: **deterministic validation wraps non-deterministic AI work**.

## The Workflow Files

Before diving into the workflow, let's understand what files we're working with:

### Input Files

**`abstracts/*.txt`** - 20 biomedical research abstracts (one per file)

Example (`abstract_001.txt`):
```
CRISPR-Cas9 Gene Editing in Hematopoietic Stem Cells for Sickle Cell Disease Treatment

Sickle cell disease is caused by a single point mutation in the beta-globin gene.
We developed a CRISPR-Cas9-based approach to correct this mutation in patient-derived
hematopoietic stem cells. Our method achieved 67% correction efficiency...
```

**`taxonomy.json`** - Controlled vocabulary of allowed keywords

```json
{
  "allowed_tags": [
    "genetics",
    "gene-editing",
    "cancer",
    "immunology",
    "neuroscience",
    "clinical-trial",
    ...
  ]
}
```

**`scripts/validate_tags.py`** - Python validation script

Checks that:
- All 20 abstracts are tagged
- Each has 2-4 tags
- All tags come from `taxonomy.json`
- JSON structure is correct

### Output File

**`tags.json`** - The agent creates this

```json
{
  "documents": [
    {
      "filename": "abstract_001.txt",
      "tags": ["genetics", "gene-editing", "clinical-trial"]
    },
    ...
  ]
}
```

## The Workflow

The workflow is at `examples/tag-documents/tag-workflow.yaml`:

```yaml
name: tag-documents
description: Tag biomedical abstracts with controlled vocabulary keywords

# Files that must exist and files to auto-sync
preconditions:
  files_exist:
    patterns:
      - abstracts/*.txt          # Test data (you provide)
      - taxonomy.json            # Config (auto-synced)
      - scripts/validate_tags.py # Script (auto-synced)
  sync_targets:
    paths:
      - taxonomy.json            # Auto-copy to workspace
      - scripts/                 # Auto-copy to workspace
    description: |
      Configuration and validation files.
      Note: abstracts/*.txt are test data and should exist in workspace.

subtasks:
  tag_abstracts:
    instructions: |
      You need to tag biomedical research abstracts with keywords.

      1. Read all .txt files in the abstracts/ directory (20 files)
      2. For each abstract, assign 2-4 relevant keywords from taxonomy.json
      3. Create tags.json with the results

      Important: Only use tags from the allowed_tags list in taxonomy.json!

    success_criteria:
      script: scripts/validate_tags.py  # Validates the output
      max_retries: 3                    # Try up to 3 times if validation fails
      retry_message: |
        Validation errors: {{error}}
        Please fix tags.json.
```

**Key parts:**

- **`files_exist`**: Checks required files before starting
- **`sync_targets`**: Auto-copies `taxonomy.json` and `scripts/` to your workspace
- **`success_criteria`**: Runs validation script after agent finishes
- **`max_retries: 3`**: Agent gets 3 chances to fix errors

## Step-by-Step Walkthrough

### Step 1: Create Your Workspace

Create a clean workspace directory:

```bash
mkdir -p ~/workspace/tag-abstracts
cd ~/workspace/tag-abstracts
```

!!! tip "Clean Workspace"
    Using a fresh directory ensures no leftover files interfere with the workflow.

### Step 2: Copy Test Data

Copy the abstracts (test data) to your workspace:

```bash
cp -r examples/tag-documents/abstracts .
```

Verify you have the files:

```bash
ls abstracts/
# Should show: abstract_001.txt through abstract_020.txt
```

!!! note "Why Only Abstracts?"
    The workflow's `sync_targets` will automatically copy `taxonomy.json` and `scripts/` for you! You only need to provide the test data.

### Step 3: Start an Agent Server

Start a Claude Code server in your workspace:

```bash
cyberian server start claude --skip-permissions --dir ~/workspace/tag-abstracts
```

This starts an agentapi server:
- **Agent**: Claude Code (recommended for this workflow)
- **Port**: 3284 (default)
- **Directory**: Your workspace
- **Skip permissions**: Allows file operations

!!! important "Server Directory"
    The server must run in the same directory where the workflow will execute (`~/workspace/tag-abstracts`).

### Step 4: Run the Workflow

Now run the workflow with auto-sync:

```bash
cyberian run \
  --workdir ~/workspace/tag-abstracts \
  examples/tag-documents/tag-workflow.yaml
```

**What happens:**

1. **Auto-sync** (before execution):
   ```
   INFO - Syncing 2 target(s) to working directory
   INFO -   Copying file: taxonomy.json
   INFO -   Copying directory: scripts/
   ```

2. **Precondition check**:
   ```
   INFO - Precondition OK: 'abstracts/*.txt' matched 20 file(s)
   INFO - Precondition OK: 'taxonomy.json' matched 1 file(s)
   INFO - Precondition OK: 'scripts/validate_tags.py' matched 1 file(s)
   ```

3. **Agent execution**:
   - Agent reads all 20 abstracts
   - Reads taxonomy.json for allowed keywords
   - Assigns 2-4 tags per abstract
   - Creates tags.json

4. **Validation**:
   - Runs `scripts/validate_tags.py`
   - Checks all constraints
   - Either succeeds or provides errors for retry

### Step 5: View the Results

Check the generated tags:

```bash
cat ~/workspace/tag-abstracts/tags.json
```

You should see structured JSON like:

```json
{
  "documents": [
    {
      "filename": "abstract_001.txt",
      "tags": ["genetics", "gene-editing", "clinical-trial"]
    },
    {
      "filename": "abstract_002.txt",
      "tags": ["quantum-physics", "structural-biology"]
    }
    ...
  ]
}
```

### Step 6: Verify All Files

See what's in your workspace now:

```bash
ls -la ~/workspace/tag-abstracts/
```

You should see:

```
abstracts/              # You provided (test data)
taxonomy.json           # Auto-synced from workflow
scripts/                # Auto-synced from workflow
tags.json              # Agent output
```

## Understanding the Key Features

### 1. Preconditions (File Validation)

```yaml
preconditions:
  files_exist:
    patterns:
      - abstracts/*.txt
      - taxonomy.json
      - scripts/validate_tags.py
```

**Purpose**: Fail fast if required files are missing
- Checked **before** task execution
- Clear error messages with hints
- Prevents cryptic errors later

### 2. Sync Targets (Auto-Copy)

```yaml
preconditions:
  sync_targets:
    paths:
      - taxonomy.json
      - scripts/
```

**Purpose**: Automatically copy config files to workspace
- Syncs **before** changing directory
- Overwrites existing files (ensures fresh copy)
- Non-fatal if file missing (just warns)

### 3. Success Criteria (External Validation)

```yaml
success_criteria:
  script: scripts/validate_tags.py
  max_retries: 3
  retry_message: |
    Validation errors: {{error}}
    Please fix tags.json.
```

**Purpose**: Deterministic validation with automatic retry
- Runs Python script after agent finishes
- Script must set `result = True/False`
- Errors fed back to agent for correction
- Up to 3 retries

## What Happens on Validation Failure

The validation script (`scripts/validate_tags.py`) performs deterministic checks:

```python
# Loads taxonomy.json to get allowed tags
with open("taxonomy.json") as f:
    allowed_tags = json.load(f)["allowed_tags"]

# Checks each document
for doc in data["documents"]:
    # Check 1: All tags must be from taxonomy.json
    invalid_tags = [tag for tag in doc["tags"] if tag not in allowed_tags]
    if invalid_tags:
        errors.append(f"  - {filename}: Invalid tags {invalid_tags}")

    # Check 2: Must have 2-4 tags
    if not (2 <= len(doc["tags"]) <= 4):
        errors.append(f"  - {filename}: Has {len(doc['tags'])} tags (must be 2-4)")

# Sets result = True/False
result = len(errors) == 0
```

If validation fails, the error is fed back to the agent:

```
Validation errors:
  - abstract_005.txt: Invalid tags ['machine-learning']
  - abstract_012.txt: Document has 5 tags (must be 2-4)

Please fix tags.json.
```

The agent reads the error, understands what's wrong, and fixes `tags.json`. This repeats up to 3 times.

## Try It Yourself: Experiment

### Experiment 1: Missing Test Data

Try running without abstracts:

```bash
mkdir -p /tmp/test-fail
cyberian run --workdir /tmp/test-fail examples/tag-documents/tag-workflow.yaml
```

**Result**: Clear error message:
```
RuntimeError: Precondition failed: No files found matching 'abstracts/*.txt'
Current directory: /tmp/test-fail
Hint: Check that required files exist or use --workdir to specify working directory
```

### Experiment 2: Different Workspace

Run in a completely different location:

```bash
mkdir -p /tmp/another-workspace
cp -r examples/tag-documents/abstracts /tmp/another-workspace/
cyberian server start claude -s --dir /tmp/another-workspace
cyberian run --workdir /tmp/another-workspace examples/tag-documents/tag-workflow.yaml
```

**Result**: Works perfectly! Auto-sync copies config files.

### Experiment 3: Multiple Runs

Run the workflow twice in the same workspace:

```bash
# First run
cyberian run --workdir ~/workspace/tag-abstracts examples/tag-documents/tag-workflow.yaml

# Second run (immediately after)
cyberian run --workdir ~/workspace/tag-abstracts examples/tag-documents/tag-workflow.yaml
```

**Result**: Second run overwrites tags.json with fresh results. Config files are re-synced (updated).

## Common Patterns

### Pattern 1: Separating Config from Data

```yaml
sync_targets:
  paths:
    - config.json       # Configuration (changes rarely)
    - scripts/          # Validation/processing scripts

files_exist:
  patterns:
    - data/*.csv        # Test data (changes per run)
    - config.json       # Must exist (synced)
```

**Benefit**: Users provide data, workflow provides config

### Pattern 2: Reproducible Validation

```yaml
success_criteria:
  script: scripts/validate.py
  max_retries: 3
  retry_message: "Errors: {{error}}"
```

**Benefit**: Deterministic validation, automatic correction

### Pattern 3: Self-Documenting Workflows

```yaml
requirements:
  agents:
    - name: claude-code
      level: RECOMMENDED
  dependencies:
    - name: python
      version: ">=3.11"
      level: REQUIRED
  notes: This workflow requires file I/O capabilities
```

**Benefit**: Users know what's needed before running

## Troubleshooting

### "No files found matching 'abstracts/*.txt'"

**Cause**: Test data not in workspace

**Fix**: Copy abstracts to your workspace:
```bash
cp -r examples/tag-documents/abstracts ~/workspace/tag-abstracts/
```

### "Connection refused" or "No server running"

**Cause**: Agent server not started

**Fix**: Start a server first:
```bash
cyberian server start claude -s --dir ~/workspace/tag-abstracts
```

### "Validation script failed"

**Cause**: Python not installed or wrong version

**Fix**: Check Python version:
```bash
python --version  # Should be 3.10+
```

## What You've Learned

You now understand:

- ✅ **Preconditions** - Validate files exist before running (fail fast)
- ✅ **Sync Targets** - Auto-copy config files to workspace
- ✅ **Success Criteria** - External validation with automatic retry
- ✅ **Workdir Management** - Control where workflows execute
- ✅ **Determinism Sandwich** - Wrap non-deterministic AI work with deterministic validation
- ✅ **Real-world Pattern** - Separating config (synced) from test data (user-provided)

## Next Steps

- **[Multi-Agent Farm](multi-agent-farm.md)** - Run multiple agents in parallel
- **[How-To: Write Workflows](../how-to/write-workflows.md)** - Advanced patterns
- **[Reference: Workflow Schema](../reference/workflow-schema.md)** - Complete YAML reference

## Key Takeaways

!!! success "Auto-Sync Saves Time"
    You only copy test data once. Config files are auto-synced on each run.

!!! success "Fail Fast is Good"
    Preconditions catch errors before wasting agent time.

!!! success "External Validation Works"
    Deterministic validation scripts ensure correctness, even with non-deterministic agents.

!!! tip "Clean Workspaces"
    Use separate workspaces for different runs to avoid confusion.
