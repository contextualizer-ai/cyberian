"""Test the cyberian-control skill files and structure."""
from pathlib import Path
import json
import yaml


class TestSkillStructure:
    """Test that the skill is properly structured."""

    def test_marketplace_json_exists(self):
        """Test that marketplace.json exists."""
        marketplace_file = Path(".claude-plugin/marketplace.json")
        assert marketplace_file.exists(), "marketplace.json should exist"

    def test_marketplace_json_valid(self):
        """Test that marketplace.json is valid JSON with required fields."""
        marketplace_file = Path(".claude-plugin/marketplace.json")
        with open(marketplace_file) as f:
            data = json.load(f)

        # Check required fields
        assert "name" in data
        assert "owner" in data
        assert "metadata" in data
        assert "plugins" in data

        # Check owner fields
        assert "name" in data["owner"]
        assert "email" in data["owner"]

        # Check metadata
        assert "description" in data["metadata"]
        assert "version" in data["metadata"]

    def test_marketplace_defines_cyberian_control(self):
        """Test that marketplace.json defines the cyberian-control plugin."""
        marketplace_file = Path(".claude-plugin/marketplace.json")
        with open(marketplace_file) as f:
            data = json.load(f)

        # Find cyberian-control plugin
        plugins = [p for p in data["plugins"] if p["name"] == "cyberian-control"]
        assert len(plugins) == 1, "Should have exactly one cyberian-control plugin"

        plugin = plugins[0]
        assert "description" in plugin
        assert "source" in plugin
        assert "skills" in plugin
        assert "./skills/cyberian-control" in plugin["skills"]

    def test_skill_md_exists(self):
        """Test that SKILL.md exists."""
        skill_file = Path("skills/cyberian-control/SKILL.md")
        assert skill_file.exists(), "SKILL.md should exist"

    def test_skill_md_has_frontmatter(self):
        """Test that SKILL.md has valid YAML frontmatter."""
        skill_file = Path("skills/cyberian-control/SKILL.md")
        with open(skill_file) as f:
            content = f.read()

        # Check for frontmatter
        assert content.startswith("---\n"), "SKILL.md should start with YAML frontmatter"

        # Extract frontmatter
        parts = content.split("---\n", 2)
        assert len(parts) >= 3, "SKILL.md should have complete frontmatter"

        frontmatter = yaml.safe_load(parts[1])

        # Check required frontmatter fields
        assert "name" in frontmatter
        assert frontmatter["name"] == "cyberian-control"
        assert "description" in frontmatter

    def test_skill_md_has_content(self):
        """Test that SKILL.md has substantial content."""
        skill_file = Path("skills/cyberian-control/SKILL.md")
        with open(skill_file) as f:
            content = f.read()

        # Should have substantial content
        assert len(content) > 1000, "SKILL.md should have substantial documentation"

        # Should mention key cyberian commands
        assert "cyberian message" in content
        assert "cyberian server" in content
        assert "cyberian farm" in content
        assert "cyberian run" in content


class TestSkillExamples:
    """Test that skill examples are properly structured."""

    def test_example_scripts_exist(self):
        """Test that example scripts exist."""
        examples_dir = Path("skills/cyberian-control/examples")
        assert examples_dir.exists(), "examples directory should exist"

        # Check for shell scripts
        assert (examples_dir / "simple-delegation.sh").exists()
        assert (examples_dir / "parallel-research.sh").exists()
        assert (examples_dir / "monitor-farm.sh").exists()

    def test_example_scripts_executable(self):
        """Test that example scripts are executable."""
        examples_dir = Path("skills/cyberian-control/examples")

        scripts = [
            "simple-delegation.sh",
            "parallel-research.sh",
            "monitor-farm.sh",
        ]

        for script in scripts:
            script_path = examples_dir / script
            assert script_path.exists()
            # Check if executable bit is set
            import os
            assert os.access(script_path, os.X_OK), f"{script} should be executable"

    def test_example_workflows_exist(self):
        """Test that example workflow YAML files exist."""
        examples_dir = Path("skills/cyberian-control/examples")

        assert (examples_dir / "multi-agent-research.yaml").exists()
        assert (examples_dir / "delegated-coding.yaml").exists()
        assert (examples_dir / "farm-config.yaml").exists()

    def test_example_workflows_valid_yaml(self):
        """Test that example workflows are valid YAML."""
        examples_dir = Path("skills/cyberian-control/examples")

        workflows = [
            "multi-agent-research.yaml",
            "delegated-coding.yaml",
            "farm-config.yaml",
        ]

        for workflow in workflows:
            workflow_path = examples_dir / workflow
            with open(workflow_path) as f:
                data = yaml.safe_load(f)
                assert data is not None, f"{workflow} should parse as valid YAML"

    def test_multi_agent_research_workflow_structure(self):
        """Test that multi-agent-research.yaml has proper structure."""
        workflow_file = Path("skills/cyberian-control/examples/multi-agent-research.yaml")
        with open(workflow_file) as f:
            data = yaml.safe_load(f)

        # Check required fields
        assert "name" in data
        assert "description" in data
        assert "params" in data
        assert "subtasks" in data

        # Check params
        assert "query" in data["params"]
        assert data["params"]["query"]["required"] is True

        # Check subtasks exist
        assert len(data["subtasks"]) > 0

    def test_delegated_coding_workflow_structure(self):
        """Test that delegated-coding.yaml has proper structure."""
        workflow_file = Path("skills/cyberian-control/examples/delegated-coding.yaml")
        with open(workflow_file) as f:
            data = yaml.safe_load(f)

        # Check required fields
        assert "name" in data
        assert "description" in data
        assert "params" in data
        assert "subtasks" in data

        # Should have multiple subtasks for different phases
        assert len(data["subtasks"]) >= 3

    def test_farm_config_structure(self):
        """Test that farm-config.yaml has proper structure."""
        farm_file = Path("skills/cyberian-control/examples/farm-config.yaml")
        with open(farm_file) as f:
            data = yaml.safe_load(f)

        # Check required fields
        assert "base_port" in data
        assert "servers" in data

        # Check servers
        assert len(data["servers"]) > 0
        for server in data["servers"]:
            assert "name" in server
            assert "agent_type" in server
            assert "directory" in server

    def test_examples_readme_exists(self):
        """Test that examples README exists."""
        readme = Path("skills/cyberian-control/examples/README.md")
        assert readme.exists()

        with open(readme) as f:
            content = f.read()

        # Should document the example files
        assert "simple-delegation.sh" in content
        assert "parallel-research.sh" in content
        assert "monitor-farm.sh" in content
        assert "multi-agent-research.yaml" in content
        assert "delegated-coding.yaml" in content
        assert "farm-config.yaml" in content


class TestSkillContent:
    """Test that skill content includes necessary information."""

    def test_skill_documents_common_commands(self):
        """Test that SKILL.md documents all major cyberian commands."""
        skill_file = Path("skills/cyberian-control/SKILL.md")
        with open(skill_file) as f:
            content = f.read()

        commands = [
            "cyberian message",
            "cyberian messages",
            "cyberian status",
            "cyberian server",
            "cyberian list-servers",
            "cyberian stop",
            "cyberian farm",
            "cyberian run",
        ]

        for cmd in commands:
            assert cmd in content, f"SKILL.md should document '{cmd}'"

    def test_skill_has_examples(self):
        """Test that SKILL.md includes example usage."""
        skill_file = Path("skills/cyberian-control/SKILL.md")
        with open(skill_file) as f:
            content = f.read()

        # Should have code blocks with examples
        assert "```bash" in content or "```yaml" in content
        assert "Examples" in content or "examples" in content

    def test_skill_explains_use_cases(self):
        """Test that SKILL.md explains when to use the skill."""
        skill_file = Path("skills/cyberian-control/SKILL.md")
        with open(skill_file) as f:
            content = f.read()

        # Should explain use cases
        assert "Use Cases" in content or "When to Use" in content
        assert "multi-agent" in content.lower() or "multiple agents" in content.lower()

    def test_skill_documents_workflow_system(self):
        """Test that SKILL.md documents the workflow system."""
        skill_file = Path("skills/cyberian-control/SKILL.md")
        with open(skill_file) as f:
            content = f.read()

        # Should document workflow features
        workflow_concepts = [
            "workflow",
            "subtasks",
            "instructions",
            "COMPLETION_STATUS",
        ]

        for concept in workflow_concepts:
            assert concept in content, f"SKILL.md should document '{concept}'"
