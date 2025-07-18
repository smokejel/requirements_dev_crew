# AI-Powered Requirements Development System

An intelligent multi-agent system built with crewAI for automated requirement decomposition and analysis. This project demonstrates how AI agents can collaborate to research topics and generate comprehensive technical reports.

## 🎯 Project Overview

This system uses multiple AI agents working in sequence to:
- Research cutting-edge developments in specified topics
- Generate detailed technical reports with findings
- Provide structured analysis and recommendations

**Default Topic**: AI Large Language Models (LLMs)
**Output**: Comprehensive markdown reports saved as `report.md`

## 🏗️ Architecture

### Core Components

- **Main Entry Point**: `src/requirement_dev/main.py`
  - Handles execution modes: run, train, replay, test
  - Manages input parameters (topic, current_year)
  
- **Crew Definition**: `src/requirement_dev/crew.py`
  - Uses crewAI's @CrewBase decorator pattern
  - Implements sequential workflow process
  - Auto-loads configurations from YAML files

- **Configuration Files**:
  - `src/requirement_dev/config/agents.yaml` - Agent definitions
  - `src/requirement_dev/config/tasks.yaml` - Task specifications

### Agent Workflow

1. **Researcher Agent**
   - Role: Senior Data Researcher
   - Goal: Uncover cutting-edge developments
   - Output: 10 structured bullet points

2. **Reporting Analyst**
   - Role: Technical Report Writer
   - Goal: Transform research into comprehensive reports
   - Output: Full markdown report

## 🚀 Installation

### Prerequisites
- Python >=3.10 <3.14
- UV package manager
- OpenAI API key

### Setup Steps

1. **Install UV package manager**:
```bash
pip install uv
```

2. **Install dependencies**:
```bash
crewai install
# or
uv install
```

3. **Configure environment**:
```bash
# Add your OpenAI API key to .env file
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

## 🎮 Usage

### Basic Commands

```bash
# Run the crew (generates report.md)
crewai run

# Alternative execution methods
uv run requirement_dev
uv run run_crew
```

### Advanced Commands

```bash
# Train the crew
uv run train <n_iterations> <filename>

# Replay specific execution
uv run replay <task_id>

# Test with parameters
uv run test <n_iterations> <eval_llm>
```

## 🔧 Customization

### Modify Agents
Edit `src/requirement_dev/config/agents.yaml` to:
- Change agent roles and goals
- Update backstories and capabilities
- Add new agent types

### Modify Tasks
Edit `src/requirement_dev/config/tasks.yaml` to:
- Define new task types
- Change expected outputs
- Update task descriptions

### Add Custom Logic
Modify `src/requirement_dev/crew.py` to:
- Add custom tools and arguments
- Implement new workflow patterns
- Integrate additional AI capabilities

### Change Default Inputs
Update `src/requirement_dev/main.py` to:
- Set different default topics
- Add new input parameters
- Modify execution logic

## 📁 Project Structure

```
src/requirement_dev/
├── main.py              # Entry point and execution modes
├── crew.py              # Crew definition and workflow
└── config/
    ├── agents.yaml      # Agent configurations
    └── tasks.yaml       # Task definitions
```

## 🔍 Understanding the System

The requirement_dev Crew operates as a sequential multi-agent system where each agent builds upon the previous agent's work. The system supports:

- **Knowledge Sources**: Integration with external data sources
- **Hierarchical Processes**: Complex workflow management
- **Tool Integration**: Custom tools and capabilities
- **Training Modes**: Iterative improvement capabilities

## Support

For support, questions, or feedback regarding the RequirementDev Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
