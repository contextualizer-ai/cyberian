import json
from pathlib import Path

result = True
error_details = []

try:
    tags_file = Path("tags.json")
    taxonomy_file = Path("taxonomy.json")
    abstracts_dir = Path("abstracts")

    # Check files exist
    if not tags_file.exists():
        result = False
        error_details.append(f"tags.json not found in {Path.cwd()}")

    if not taxonomy_file.exists():
        result = False
        error_details.append(f"taxonomy.json not found in {Path.cwd()}")

    if not abstracts_dir.exists():
        result = False
        error_details.append(f"abstracts/ directory not found in {Path.cwd()}")

    if not result:
        # Raise exception with diagnostic info
        raise FileNotFoundError(" | ".join(error_details))

    # Load files
    with open(tags_file) as f:
        data = json.load(f)

    with open(taxonomy_file) as f:
        taxonomy = json.load(f)

    # Validate structure
    if "documents" not in data:
        raise ValueError("tags.json missing 'documents' key")

    if "allowed_tags" not in taxonomy:
        raise ValueError("taxonomy.json missing 'allowed_tags' key")

    docs = data["documents"]
    allowed = set(taxonomy["allowed_tags"])

    # Count abstract files
    abstract_files = []
    for file_path in abstracts_dir.glob("*.txt"):
        abstract_files.append(file_path.name)

    # Validate counts
    if len(docs) != len(abstract_files):
        raise ValueError(f"Document count mismatch: {len(docs)} tagged vs {len(abstract_files)} files in abstracts/")

    # Validate each document
    expected_files = set(abstract_files)
    tagged_files = set()

    for doc in docs:
        if "filename" not in doc:
            raise ValueError(f"Document missing 'filename' key: {doc}")

        if "tags" not in doc:
            raise ValueError(f"Document missing 'tags' key: {doc['filename']}")

        filename = doc["filename"]
        tagged_files.add(filename)
        tags = doc["tags"]

        # Validate tag count
        if len(tags) < 2:
            raise ValueError(f"{filename}: only {len(tags)} tag(s), need 2-4")

        if len(tags) > 4:
            raise ValueError(f"{filename}: {len(tags)} tags, maximum is 4")

        # Validate tags are from taxonomy
        for tag in tags:
            if tag not in allowed:
                raise ValueError(f"{filename}: invalid tag '{tag}' not in taxonomy")

    # Check all files are tagged
    if tagged_files != expected_files:
        missing = expected_files - tagged_files
        extra = tagged_files - expected_files

        errors = []
        if missing:
            errors.append(f"missing: {sorted(missing)}")
        if extra:
            errors.append(f"extra: {sorted(extra)}")

        raise ValueError(f"File mismatch - {' | '.join(errors)}")

    # All validations passed
    result = True

except Exception as e:
    # If we hit an exception, set result to False
    # Store the error message for potential debugging
    result = False
    error_message = str(e)
