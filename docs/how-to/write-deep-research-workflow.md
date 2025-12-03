# How to Write a Deep Research Workflow

This guide shows you how to build a multi-step deep research workflow using cyberian, based on modern deep research agent patterns.

## What is Deep Research?

According to recent research, true deep research agents are autonomous AI systems with sophisticated capabilities:

- **Dynamic reasoning & planning** - Adaptive long-horizon planning that adjusts based on findings
- **Multi-hop information retrieval** - Following citation chains, synthesizing across multiple sources
- **Browser-based exploration** - Not just API calls, but autonomous web interaction
- **Code execution & tool use** - Running analyses, processing data, invoking specialized tools
- **Structured synthesis** - Producing organized, well-cited reports with transparent reasoning

As of 2025, systems like [OpenAI's Deep Research](https://openai.com/index/introducing-deep-research/), [Google's Gemini Deep Research](https://gemini.google/overview/deep-research/), and [Microsoft's Researcher](https://www.microsoft.com/en-us/microsoft-365/blog/2025/03/25/introducing-researcher-and-analyst-in-microsoft-365-copilot/) can autonomously search hundreds of sources, perform multi-step analysis, and generate comprehensive reports.

## A Simple Iterative Research Workflow

The workflow in `tests/examples/deep-research.yaml` is a **simplified version** focused on the core pattern of iterative research:

```
┌─────────────────────┐
│  Initial Search     │  → Create research plan, start report
└─────────────────────┘
          ↓
┌─────────────────────┐
│  Iterate Loop       │  → Follow plan, gather sources, refine
└─────────────────────┘  ↑
          ↓              │
    [Loop until          │
     exhausted] ─────────┘
```

**What this workflow does:**
- ✅ Iterative research with loop-until-exhausted pattern
- ✅ Structured file organization (plan, report, citations)
- ✅ Manual citation tracking via agent instructions
- ✅ Agent decides when research is complete

**What it doesn't do (yet):**
- ❌ Multi-hop retrieval (no automatic citation following)
- ❌ Dynamic re-planning (plan is updated manually by agent, not automatically)
- ❌ Browser automation (relies on agent's web capabilities)
- ❌ Code execution for analysis (just file organization)

This is a **good starting point** for building research workflows, but not a full deep research system.

## Complete Workflow

Here's the full workflow with detailed annotations:

```yaml
name: deep-research
description: Iteratively perform deep research on a topic

requires_workdir: true  # Must specify --workdir for outputs

params:
  query:
    range: string
    required: true
    examples:
      - "CRISPR applications in 2024"
      - "quantum computing error correction"

  workdir:
    range: string
    required: true
    examples:
      - "/tmp/research-output"

subtasks:
  # Phase 1: Initial search and planning
  initial_search:
    instructions: |
      Perform deep research on {{query}}.
      Keep all files in {{workdir}}.

      ## Start with a Plan

      Always start by writing a research plan in `PLAN.md`:
      - Key questions to investigate
      - Search strategies
      - Types of sources needed
      - How to structure the final report

      ## Create the Report

      Maintain a report in `REPORT.md`. Update this as you go along.
      Structure:
      - Executive summary
      - Main findings (organized by theme)
      - Citation graph insights
      - Open questions

      ## Organize Citations

      Create a `citations/` folder with files named like:
      `smith-2002-autophagy-paper.pdf` (if PDF available)
      `smith-2002-autophagy-fulltext.txt` (converted text, MUST be actual)
      `smith-2002-autophagy-summary.md` (YOUR summary)
      `jones-2003-regulation-abstract.md` (MUST be actual abstract)
      `jones-2003-regulation-summary.md` (YOUR summary)

      ## Track Citation Relationships

      Maintain `CITATION_GRAPH.md` with entries like:
      `* [smith-2002] cites [jones-2003] claiming "X regulates Y"`

      This helps identify:
      - Seminal papers (heavily cited)
      - Emerging ideas (recent citations)
      - Controversies (conflicting claims)

      ## Citation Rules

      - Always cite in report: "Some finding[smith-2002-autophagy]"
      - Get full text when available (never fabricate it)
      - Default to abstracts if full text unavailable
      - Use suffixes to denote type: `-paper.pdf`, `-abstract.md`, `-summary.md`
      - Your summaries go in `-summary.md`, actual content in other files

      ## Additional Notes

      You can create additional notes files as needed:
      - `METHODOLOGY_NOTES.md`
      - `KEY_FINDINGS.md`
      - `CONTRADICTIONS.md`

  # Phase 2: Iterative deepening
  iterate:
    instructions: |
      Continue researching {{query}}, following the plan in `PLAN.md`.

      For each iteration:
      1. Check `PLAN.md` for next research direction
      2. Search for relevant sources
      3. Read and summarize new papers
      4. Update `CITATION_GRAPH.md` with new relationships
      5. Update `REPORT.md` with new findings
      6. Update `PLAN.md` if new directions emerge

      Keep iterating until you've:
      - Covered all major perspectives on the topic
      - Followed key citation chains
      - Addressed the main questions in PLAN.md
      - Identified remaining open questions

      When research is exhausted, yield:
      COMPLETION_STATUS: NO_MORE_RESEARCH

    loop_until:
      status: NO_MORE_RESEARCH
      message: |
        If you think all research avenues are exhausted, then
        yield status NO_MORE_RESEARCH
```

## How It Works

### Phase 1: Initial Search

The agent:
1. Creates a research plan (`PLAN.md`)
2. Performs initial searches
3. Sets up the file structure
4. Begins the report
5. Downloads and organizes first batch of sources

### Phase 2: Iterative Loop

The agent repeatedly:
1. Checks the plan for next steps
2. Searches for new sources
3. Reads and extracts information
4. Updates citation graph
5. Refines the report
6. Updates plan if new directions discovered

The loop continues until the agent determines research is exhausted.

## File Structure Example

After running, your workspace will look like:

```
/tmp/research-crispr/
├── PLAN.md                          # Research strategy
├── REPORT.md                        # Main findings
├── CITATION_GRAPH.md                # Citation relationships
└── citations/
    ├── doudna-2012-crispr-paper.pdf
    ├── doudna-2012-crispr-fulltext.txt
    ├── doudna-2012-crispr-summary.md
    ├── zhang-2013-genome-abstract.md
    ├── zhang-2013-genome-summary.md
    └── cong-2013-multiplex-abstract.md
```

## Running the Workflow

### Basic Run

```bash
# Create workspace
mkdir -p /tmp/research-output

# Start agent server
cyberian server start claude --skip-permissions --dir /tmp/research-output

# Run research
cyberian run tests/examples/deep-research.yaml \
  --workdir /tmp/research-output \
  --param query="CRISPR gene editing applications 2024" \
  --param workdir="/tmp/research-output"
```

### With Custom Timeout

Deep research can take time. Increase timeout if needed:

```bash
cyberian run tests/examples/deep-research.yaml \
  --workdir /tmp/research-output \
  --param query="quantum error correction" \
  --param workdir="/tmp/research-output" \
  --timeout 3600  # 1 hour
```

### Monitoring Progress

Watch the report as it evolves:

```bash
# In another terminal
watch -n 5 cat /tmp/research-output/REPORT.md
```

## Key Design Patterns

### 1. Structured File Organization

**Why it matters:** Enables the agent to track sources, avoid duplication, and cite properly.

```yaml
citations/
  smith-2002-autophagy-paper.pdf      # Original source
  smith-2002-autophagy-fulltext.txt   # Extracted text (actual)
  smith-2002-autophagy-summary.md     # Agent's summary
```

The naming convention (`author-year-topic-type`) makes it easy to:
- Identify sources at a glance
- Avoid duplicate downloads
- Know what you have (abstract vs. full text)

### 2. Citation Graph Tracking

**Why it matters:** Reveals research landscape structure.

```markdown
# CITATION_GRAPH.md
* [doudna-2012] cites [jinek-2012] for "RNA-guided DNA cleavage"
* [zhang-2013] cites [doudna-2012] for "CRISPR system"
* [cong-2013] cites [doudna-2012] for "Cas9 mechanism"
```

This helps identify:
- **Seminal papers** - Heavily cited (e.g., doudna-2012)
- **Research fronts** - Recent work with few citations
- **Consensus vs. debate** - Competing claims

### 3. Living Research Plan

**Why it matters:** Research is non-linear. Plans must adapt.

```markdown
# PLAN.md

## Initial Questions
1. What are current CRISPR applications?
2. What are the limitations?

## Search Strategy
- Start with recent reviews (2023-2024)
- Follow citations to seminal papers
- Check clinical trials databases

## Emerging Directions (added during iteration)
4. NEW: Base editing vs. prime editing comparison
5. NEW: Delivery mechanisms (AAV vs. LNP)
```

The agent updates this as new directions emerge.

### 4. Loop Until Exhausted

**Why it matters:** Research depth varies by topic.

```yaml
loop_until:
  status: NO_MORE_RESEARCH
  message: |
    If you think all research avenues are exhausted, then
    yield status NO_MORE_RESEARCH
```

The agent decides when to stop based on:
- Coverage of main questions
- Depth of citation chains followed
- Diminishing returns on new searches


## Comparison to 2025 Deep Research Systems

Here's how this simple workflow compares to production deep research systems:

| Feature | OpenAI Deep Research | Gemini Deep Research | This Workflow |
|---------|---------------------|---------------------|---------------|
| Multi-step planning | ✓ (reasoning model) | ✓ (continuous loop) | Partial (agent updates plan) |
| Multi-hop retrieval | ✓ (automatic) | ✓ (automatic) | ✗ (manual citation following) |
| Browser automation | ✓ | ✓ | ✗ (relies on agent capabilities) |
| Citation tracking | ✓ (automatic) | ✓ (automatic) | Partial (agent writes to files) |
| Iterative refinement | ✓ | ✓ | ✓ (loop_until) |
| Structured output | ✓ (reports) | ✓ (multi-page) | ✓ (REPORT.md) |
| Dynamic re-planning | ✓ (adaptive) | ✓ (adaptive) | ✗ (static workflow) |
| Code execution | ✓ | ✓ | ✗ (not implemented) |
| Human oversight | ✓ (approve queries) | ✓ | ✓ (inspect workspace) |
| Transparency | ✓ (show sources) | ✓ (auditable) | ✓ (all files saved) |

**What this workflow provides:**
- Simple, understandable pattern for iterative research
- Full control over file organization and structure
- Transparent process (all intermediate files saved)
- Easy to customize and extend
- Works with any agent that can read/write files

**What's missing (compared to full deep research systems):**
- Automatic citation graph traversal
- Dynamic workflow adaptation
- Specialized retrieval tools (e.g., academic databases)
- Automated source quality assessment
- Multi-agent coordination

## Tips and Best Practices

### Tip 1: Start with Focused Queries

**Good:**
```bash
--param query="CRISPR base editing for sickle cell disease"
```

**Too broad:**
```bash
--param query="gene therapy"
```

Focused queries lead to deeper, more useful reports.

### Tip 2: Monitor the Citation Graph

```bash
# Check what's being cited
cat /tmp/research-output/CITATION_GRAPH.md | grep "\[" | sort | uniq -c
```

This reveals which papers are central to the topic.

### Tip 3: Resume from Interruptions

If the workflow stops, you can resume:

```bash
# First run (interrupted)
cyberian run deep-research.yaml --workdir /tmp/research-output --param query="..."

# Resume (agent sees existing PLAN.md, REPORT.md, and continues)
cyberian run deep-research.yaml --workdir /tmp/research-output --param query="..."
```

The agent will see existing files and continue from where it left off.

### Tip 4: Use Version Control

```bash
cd /tmp/research-output
git init
git add .
git commit -m "Initial research snapshot"

# After each major update
git commit -am "Added 5 more papers on base editing"
```

This lets you track how understanding evolved.

## Common Issues

### Issue: Agent stops too early

**Cause:** Agent thinks research is exhausted

**Solution:** Make loop condition more specific:

```yaml
loop_until:
  status: NO_MORE_RESEARCH
  message: |
    Only yield NO_MORE_RESEARCH if:
    1. You've covered all questions in PLAN.md
    2. You've followed at least 3 citation levels deep
    3. You've examined at least 20 sources
    4. Recent searches return no new relevant papers
```

### Issue: Citation files not organized

**Cause:** Agent not following naming convention

**Solution:** Be more explicit in instructions:

```yaml
CRITICAL: File naming must follow this exact pattern:
  {author}-{year}-{keyword}-{type}.{ext}

Examples:
  ✓ smith-2002-autophagy-paper.pdf
  ✓ jones-2023-crispr-abstract.md
  ✗ paper1.pdf (wrong - no structure)
  ✗ Smith et al 2002.pdf (wrong - spaces, capitals)
```

### Issue: Duplicates being downloaded

**Cause:** Agent not checking existing files

**Solution:** Add explicit check in instructions:

```yaml
Before downloading any paper:
1. Check if it already exists in citations/
2. Check CITATION_GRAPH.md for the citation
3. Only download if truly new
```

## Related Guides

- [Tag Documents Walkthrough](../tutorials/tag-documents-walkthrough.md) - Validation patterns
- [Use Templates](use-templates.md) - Advanced Jinja2 templating
- [Provider Calls](provider-calls.md) - External API integration
- [Troubleshooting](troubleshooting.md) - Workflow debugging

## Sources

- [Introducing deep research | OpenAI](https://openai.com/index/introducing-deep-research/)
- [Introducing Researcher and Analyst in Microsoft 365 Copilot | Microsoft 365 Blog](https://www.microsoft.com/en-us/microsoft-365/blog/2025/03/25/introducing-researcher-and-analyst-in-microsoft-365-copilot/)
- [Deep Research Agents: A Systematic Roadmap - arXiv](https://arxiv.org/abs/2506.18096)
- [Gemini Deep Research — your personal research assistant](https://gemini.google/overview/deep-research/)
- [Introducing Deep Research in Azure AI Foundry Agent Service | Microsoft Azure Blog](https://azure.microsoft.com/en-us/blog/introducing-deep-research-in-azure-ai-foundry-agent-service/)
