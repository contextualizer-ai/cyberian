# Document Tagging Workflow Example

This example demonstrates the **"determinism sandwich" pattern** for reliable agent workflows:

1. **Deterministic Input**: 20 biomedical research abstracts + controlled vocabulary taxonomy
2. **Non-Deterministic Processing**: Agent reads abstracts and assigns relevant tags
3. **Deterministic Validation**: External Python script validates all constraints
4. **Deterministic Feedback**: Validation errors are fed back to agent for retry

## Files

```
tag-documents/
├── README.md                  # This file
├── tag-workflow.yaml          # Workflow definition
├── taxonomy.json              # Controlled vocabulary (20 allowed tags)
├── abstracts/                 # 20 biomedical research abstracts
│   ├── abstract_001.txt       # CRISPR gene editing
│   ├── abstract_002.txt       # Quantum physics
│   ├── ...
│   └── abstract_020.txt       # Optogenetics
└── scripts/
    └── validate_tags.py       # External validation script
```

## The Determinism Sandwich

### Layer 1: Deterministic Input
- 20 abstract files (fixed content)
- Controlled vocabulary taxonomy with 20 allowed tags
- Clear constraints: 2-4 tags per document, tags must be from taxonomy

### Layer 2: Non-Deterministic Work
Agent must:
- Read each abstract
- Understand the research topic
- Select 2-4 most relevant tags from taxonomy
- Create `tags.json` with all 20 documents tagged

### Layer 3: Deterministic Validation
The `validate_tags.py` script checks:
- ✓ `tags.json` exists and is valid JSON
- ✓ All 20 abstracts are tagged
- ✓ Every tag is from the allowed taxonomy
- ✓ Each document has 2-4 tags
- ✓ JSON matches expected schema

### Layer 4: Deterministic Feedback
If validation fails:
- Error message explains what's wrong
- Agent gets specific feedback (e.g., "abstract_005.txt: invalid tags {'quantum-mechanics'}. Must use only: genetics, cancer, ...")
- Agent retries with corrected understanding
- Maximum 3 retries

## Running the Workflow

```bash
cd tests/examples/tag-documents

# Run the workflow
cyberian run tag-workflow.yaml --dir .

# Or with specific agent
cyberian run tag-workflow.yaml --dir . --agent-type claude
```

## Expected Output

After successful execution, you'll have:

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

## Key Features Demonstrated

### 1. External Success Criteria Script

Instead of embedding Python in YAML:

```yaml
success_criteria:
  script: scripts/validate_tags.py  # Clean separation of concerns
  max_retries: 3
```

### 2. Informative Error Feedback

The validation script provides detailed errors:

```
VALIDATION ERRORS:
  - abstract_005.txt: invalid tags {'metabolism-disorders'}. Must use only: genetics, cancer, ...
  - abstract_012.txt: must have at least 2 tags, has 1
  - Missing tags for files: abstract_018.txt, abstract_019.txt
```

### 3. No Completion Status in Instructions

Notice the instructions DON'T include `COMPLETION_STATUS: COMPLETE`. The agent just does the work, and success criteria determine if it's done correctly.

### 4. Retry with Context

If validation fails, the agent sees the exact errors and can fix them. The `retry_message` template injects validation errors:

```yaml
retry_message: |
  Your tagging had validation errors:

  {{error}}

  Please review the errors and fix your tags.json file.
```

## Why This Pattern Works

1. **Clear Success Criteria**: Agent knows exactly what "done" means
2. **Automated Verification**: No human needed to check each tag
3. **Self-Correcting**: Agent can fix errors based on feedback
4. **Scalable**: Works for 20 files or 2,000 files
5. **Maintainable**: Validation logic is separate Python code, easy to test

## Extending This Pattern

This pattern works for many tasks:

- **Code migration**: Perl → Python with compilation checks
- **Format conversion**: Markdown → RST with parse validation
- **Test generation**: Functions → tests with pytest collection check
- **Documentation**: API routes → OpenAPI spec with schema validation
- **Data transformation**: CSV → JSON with schema validation

The key is:
1. Deterministic input
2. Clear constraints
3. Automated validation
4. Informative feedback

## Testing

The workflow has comprehensive tests:

```bash
# Run all tests
pytest tests/test_tag_workflow.py -v

# Run specific test
pytest tests/test_tag_workflow.py::test_validation_script_catches_errors -v
```

See `tests/test_tag_workflow.py` for test implementation.
