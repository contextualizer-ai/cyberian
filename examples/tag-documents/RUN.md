# Running the Tag Documents Example

This example demonstrates the "determinism sandwich" pattern for reliable agent workflows.

## Quick Start

```bash
# Navigate to this directory
cd examples/tag-documents

# Run the workflow
uv run cyberian run tag-workflow.yaml
```

## What This Does

The agent will:
1. Read all 20 biomedical abstracts in `abstracts/`
2. Read the controlled vocabulary from `taxonomy.json`
3. Assign 2-4 relevant tags to each abstract
4. Create `tags.json` with all tagged documents

The validation script (`scripts/validate_tags.py`) checks:
- ✓ All 20 abstracts are tagged
- ✓ Each document has 2-4 tags
- ✓ All tags come from the allowed taxonomy
- ✓ JSON structure is correct

If validation fails, the agent gets detailed error messages and can retry (up to 3 times).

## Files in This Example

```
tag-documents/
├── README.md              # Detailed explanation of the pattern
├── RUN.md                 # This file
├── tag-workflow.yaml      # Workflow definition
├── taxonomy.json          # Allowed tags (20 keywords)
├── abstracts/             # 20 biomedical research abstracts
│   ├── abstract_001.txt   # CRISPR gene editing
│   ├── abstract_002.txt   # Quantum physics
│   ├── ...
│   └── abstract_020.txt   # Optogenetics
└── scripts/
    └── validate_tags.py   # External validation script

Output:
└── tags.json              # Created by agent (validated)
```

## Expected Output

After successful run, you'll have a `tags.json` file like:

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
    },
    ...
  ]
}
```

## Troubleshooting

If the workflow fails:

1. **Check the error message** - The validation script provides detailed feedback
2. **Review tags.json** (if created) - See what the agent produced
3. **Check abstracts are readable** - Ensure all 20 .txt files exist
4. **Verify taxonomy.json** - Should have "allowed_tags" list

## See Also

- See [README.md](README.md) for detailed explanation of the determinism sandwich pattern
- See [../../docs/how-to/write-workflows.md](../../docs/how-to/write-workflows.md) for workflow syntax
