# Multi-Agent Role-based Code Reviewer System

A structured, multi-agent pipeline for collaborative **AI-assisted code review**.  
This system orchestrates three specialized agents — **Junior**, **Senior**, and **Manager** — to simulate a realistic peer review process, producing multi-layered feedback in Markdown reports.

---

## Overview

The review process is managed by a central **Manager Agent**, which coordinates the following steps:

1. **Junior Developer Agent**  
   Reviews code like a peer engineer — raising questions, confusion points, and small suggestions.

2. **Senior Developer Agent**  
   Reviews the same code, answering the junior’s questions and offering deeper technical or architectural insights.

3. **Manager Agent**  
   Synthesizes both perspectives into a final actionable review summary, delivered to the user.

Each agent’s response is stored separately as Markdown files for traceability and quality control.

---

## ⚙️ Workflow Diagram

```text
┌───────────────┐
│  User / CLI   │
│  ("Do a code  │
│   review")    │
└──────┬────────┘
       │  (file_path + user_input)
       v
┌─────────────────────┐
│   manager_agent      │
│  (orchestrator)      │
└──────┬───────┬───────┘
       │       │
       │       │
       │       v
       │   ┌───────────────────────┐
       │   │ junior_developer_agent│
       │   │  - asks questions     │
       │   │  - flags concerns     │
       │   └──────────┬────────────┘
       │              │
       │    (junior_notes[], call_id J)
       │              │
       │              v
       │   ┌───────────────────────┐
       │   │ senior_developer_agent│
       │   │  - answers junior     │
       │   │  - gives guidance     │
       │   └──────────┬────────────┘
       │              │
       │    (senior_notes[], call_id S)
       │              │
       v              │
┌─────────────────────┐
│   manager_agent      │
│   synthesizes        │
│   - summarizes junior│
│   - injects senior   │
│   - gives next steps │
└─────────┬────────────┘
          │
          v
   manager_notes[]
          │
          v
  (final_output to user)
          |--> console stdout
          |--> reviews/<file>/manager_review.md
          |--> reviews/<file>/junior_review.md
          |--> reviews/<file>/senior_review.md
          |--> (optional - sanity check) reviews/<file>/planner_review.md
````

---

## 🧩 File Generation

After each run, the system automatically creates a structured directory:

```bash
reviews/
└── (recursive two repo names)_(file name)/
    ├── junior_review.md
    ├── senior_review.md
    ├── manager_review.md
    └── planner_review.md   # internal reasoning trace (optional - remove for production)
```

Each file contains Markdown-formatted feedback written by its respective agent.

---

## 🧠 Agent Responsibilities

| Agent                      | Role                                                                               | Output              |
| -------------------------- | ---------------------------------------------------------------------------------- | ------------------- |
| **Junior Developer Agent** | Identifies unclear code segments, asks questions, and flags simple issues.         | `junior_review.md`  |
| **Senior Developer Agent** | Answers junior’s questions, reviews architecture, and recommends improvements.     | `senior_review.md`  |
| **Manager Agent**          | Aggregates both reviews and provides a unified summary with actionable next steps. | `manager_review.md` |
| **Planner (optional)**     | Captures the manager’s reasoning and tool orchestration for debugging.             | `planner_review.md` |

---

## 💻 Usage

### 1. Clone and Install

```bash
git clone https://github.com/ikhyunAn/RoleBased_CodeReviewer_MVP.git
cd RoleBased_CodeReviewer_MVP
python3 -m venv venv # Optional: Virtual environment to contain installed packages
pip install -r requirements.txt
```

### 2. Configure

Create a `.env` file in the root directory:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run the Review

```bash
python agent.py "Please review this code" ./examples/my_script.py
```

Output appears in the console and as Markdown files under `reviews/<dirname_filename>/`.

---

## 🧾 Example Output

**Manager Review (Structure Example)**

```markdown
# Manager Notes

### Summary
(junior dev concerns)...

### Senior dev answers and guidance (condensed)

### Concrete, copy-paste suggestions (next steps)

### Recommended next steps (prioritized)

```

**Junior Review (Structure Example)**

```markdown
# Junior Developer Review

Nice and concise main! I have some peer-level feedback, small suggestions, and ...

### High-level summary
...

### Suggestions / possible improvements
...

### Questions (a lot — I want to understand design choices)
...

```

**Senior Review (Structure Example)**

```markdown
# Senior Developer Review

### Overall:
this is a perfectly reasonable, ...

### Summary of primary issues and suggestions
...

### Suggested refactor examples
...

### Answers to your questions (1–20)
...
```
---

## 🛠️ Project Structure

```text
.
├── agent.py                # main orchestration script
├── requirements.txt
├── .env                    # contains OPENAI_API_KEY
├── reviews/                # output directory
│   └── <source_file>/      # per-file review results
│       ├── junior_review.md
│       ├── senior_review.md
│       ├── manager_review.md
│       └── planner_review.md
└── README.md
```

---

## Debugging & Developer Notes

* All agent interactions (`tool_call_item`, `tool_call_output_item`, etc.) are logged to stdout for tracing.
* `planning_notes` capture the manager’s internal reasoning (optional, for auditing).
* The code gracefully handles file creation via `os.makedirs(review_dir, exist_ok=True)`.

---

## Future Improvements

### Phase 1:
- [ ] Parallel execution of reviewer agents.
- [ ] Configurable agent personalities and model sizes.

### Phase 2:
- [ ] Support for code diff context (not just full files).
- [ ] Support for all files inside given directory (not just single file).

### Phase 3: Github
- [ ] Integration with GitHub PR comments for auto-posting results.
---

## 📜 License

MIT License © 2025 Ikhyun An (John)

---

## Contributing

For major changes, open an issue first to discuss your ideas.

---

## Acknowledgments

Built using the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)