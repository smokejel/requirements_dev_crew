# Streamlined CrewAI Requirements Decomposition Framework
## 5-Agent Architecture for Maximum Efficiency

### Knowledge Repository Setup

```python
from crewai import Knowledge, FileKnowledgeSource, Crew, Agent, Task, Process

# Knowledge sources
knowledge_sources = [
    FileKnowledgeSource(
        file_path="./documents/srs.pdf",
        metadata={"type": "requirements", "document": "SRS"}
    ),
    FileKnowledgeSource(
        file_path="./documents/icd.pdf", 
        metadata={"type": "interfaces", "document": "ICD"}
    ),
    FileKnowledgeSource(
        file_path="./documents/standards.md",
        metadata={"type": "standards", "document": "best_practices"}
    ),
    FileKnowledgeSource(
        file_path="./documents/architecture.pdf",
        metadata={"type": "architecture", "document": "system_design"}
    )
]

knowledge = Knowledge(sources=knowledge_sources)
```

## Agent Definitions

### 1. Requirements Analyst Agent
**Role:** Requirements extraction, parsing, and categorization
**Consolidates:** Document analysis + Requirements parsing

```python
requirements_analyst = Agent(
    role="Requirements Analyst",
    goal="Extract, parse, and categorize all requirements from specification documents using knowledge repository context",
    backstory="""You are a senior requirements engineer with 15+ years experience in 
    systems analysis. You excel at distinguishing requirements from descriptive text, 
    understanding system boundaries from architecture documents, and extracting relevant 
    contextual information from complex technical documents. You create structured 
    requirement inventories that serve as the foundation for decomposition.""",
    verbose=True,
    knowledge=knowledge,
    tools=[knowledge_search_tool, requirement_extraction_tool],
    max_iter=3
)
```

### 2. Decomposition Strategist Agent
**Role:** Strategy development and requirement allocation
**Consolidates:** Strategy planning + Architecture mapping

```python
decomposition_strategist = Agent(
    role="Decomposition Strategist", 
    goal="Develop optimal decomposition strategy and allocate requirements to appropriate subsystems",
    backstory="""You are a systems architect and decomposition expert who translates 
    system-level requirements into logical subsystem allocations. You understand various 
    decomposition methodologies, can analyze system architectures to determine optimal 
    boundaries, and create clear allocation rules. Your strategic approach ensures complete 
    coverage without overlap.""",
    verbose=True,
    knowledge=knowledge,
    tools=[knowledge_search_tool, strategy_planning_tool, architecture_mapping_tool],
    max_iter=3
)
```

### 3. Requirements Engineer Agent
**Role:** Detailed requirement decomposition and refinement
**Consolidates:** Functional + Non-functional + Interface decomposition

```python
requirements_engineer = Agent(
    role="Requirements Engineer",
    goal="Execute detailed decomposition of functional, non-functional, and interface requirements following the established strategy",
    backstory="""You are a specialized requirements engineer with expertise in breaking 
    down complex system requirements into precise, testable subsystem requirements. You 
    handle functional decomposition, performance allocation, interface specification, and 
    ensure all requirements are clear, measurable, and implementable. You maintain the 
    technical rigor needed for safety-critical systems.""",
    verbose=True,
    knowledge=knowledge,
    tools=[knowledge_search_tool, functional_analysis_tool, interface_analysis_tool, performance_allocation_tool],
    max_iter=4
)
```

### 4. Quality Assurance Agent  
**Role:** Validation, verification, and compliance checking
**Consolidates:** Quality assurance + Compliance verification + Traceability

```python
quality_assurance_agent = Agent(
    role="Quality Assurance Specialist",
    goal="Ensure all decomposed requirements meet quality standards, compliance requirements, and maintain complete traceability",
    backstory="""You are a quality and compliance expert with deep knowledge of requirements 
    standards, regulatory compliance, and traceability management. You validate requirement 
    quality using industry best practices, ensure compliance with applicable standards, 
    and maintain rigorous traceability matrices. Your work prevents costly downstream 
    issues and ensures certification readiness.""",
    verbose=True,
    knowledge=knowledge,
    tools=[knowledge_search_tool, quality_validation_tool, compliance_check_tool, traceability_tool],
    max_iter=3
)
```

### 5. Documentation Specialist Agent
**Role:** Professional output formatting and deliverable creation
**Consolidates:** Output formatting + Documentation generation

```python
documentation_specialist = Agent(
    role="Documentation Specialist",
    goal="Create professional, well-formatted requirement documents and deliverable packages for stakeholders",
    backstory="""You are a technical documentation expert who transforms complex requirement 
    analyses into clear, professional documents. You ensure consistent formatting, logical 
    organization, and stakeholder-appropriate presentation. Your documents become the 
    authoritative source for development teams and serve as the baseline for all subsequent 
    work.""",
    verbose=True,
    knowledge=knowledge,
    tools=[knowledge_search_tool, formatting_tool, document_generation_tool],
    max_iter=2
)
```

## Task Definitions

### Task 1: Requirements Extraction and Analysis
```python
requirements_extraction_task = Task(
    description="""Extract and analyze all requirements from the primary specification 
    document. Use knowledge repository to understand system context, architecture, and 
    applicable standards.
    
    Actions:
    1. Search knowledge repository for system architecture and boundaries
    2. Extract requirements from primary specification
    3. Categorize requirements (functional, non-functional, interface, constraints)
    4. Identify requirement dependencies and cross-references
    5. Create structured requirement inventory with context annotations
    
    Primary Specification: {primary_specification}
    Target System: {target_system}""",
    expected_output="""Structured requirements inventory containing:
    - Complete list of categorized requirements
    - System context summary from knowledge repository
    - Requirement dependency mapping
    - Initial quality assessment
    - Recommendations for decomposition approach""",
    agent=requirements_analyst
)
```

### Task 2: Context Analysis and Architecture Mapping
```python
context_analysis_task = Task(
    description="""Analyze system architecture and create comprehensive context for 
    decomposition strategy development.
    
    Actions:
    1. Extract system architecture and subsystem boundaries
    2. Identify interface specifications and constraints
    3. Review applicable standards and best practices
    4. Map requirements to architectural components
    5. Create context framework for decomposition
    
    Requirements Inventory: {requirements_inventory}""",
    expected_output="""Context analysis report containing:
    - System architecture overview with subsystem boundaries
    - Interface specifications and constraints
    - Applicable standards checklist
    - Initial requirement-to-architecture mapping
    - Decomposition strategy recommendations""",
    agent=decomposition_strategist,
    context=[requirements_extraction_task]
)
```

### Task 3: Decomposition Strategy Development
```python
strategy_development_task = Task(
    description="""Develop comprehensive decomposition strategy based on architecture 
    analysis and requirements inventory.
    
    Actions:
    1. Select optimal decomposition approach (functional/architectural/hybrid)
    2. Define subsystem allocation rules and criteria
    3. Create requirement templates for each subsystem
    4. Establish validation criteria and quality gates
    5. Plan decomposition workflow and dependencies
    
    Context Analysis: {context_analysis}
    Requirements Inventory: {requirements_inventory}""",
    expected_output="""Decomposition strategy document containing:
    - Decomposition methodology and rationale
    - Subsystem allocation rules and criteria
    - Requirement templates by subsystem type
    - Validation criteria and quality gates
    - Execution workflow plan""",
    agent=decomposition_strategist,
    context=[requirements_extraction_task, context_analysis_task]
)
```

### Task 4: Functional Requirements Decomposition  
```python
functional_decomposition_task = Task(
    description="""Decompose functional requirements into subsystem-level requirements 
    following the established strategy.
    
    Actions:
    1. Apply functional decomposition methodology
    2. Allocate functions to appropriate subsystems
    3. Ensure functional completeness and non-overlap
    4. Create detailed functional requirement statements
    5. Maintain traceability to parent requirements
    
    Decomposition Strategy: {decomposition_strategy}""",
    expected_output="""Functional subsystem requirements containing:
    - Complete set of subsystem functional requirements
    - Functional allocation matrix
    - Traceability links to parent requirements
    - Functional coverage verification
    - Initial quality assessment""",
    agent=requirements_engineer,
    context=[strategy_development_task]
)
```

### Task 5: Non-Functional Requirements Decomposition
```python
nonfunctional_decomposition_task = Task(
    description="""Decompose and allocate non-functional requirements to subsystems.
    
    Actions:
    1. Identify system-level performance, reliability, security requirements
    2. Allocate performance budgets and quality attributes to subsystems
    3. Create measurable acceptance criteria
    4. Ensure requirements are testable and verifiable
    5. Document allocation rationale and assumptions
    
    Decomposition Strategy: {decomposition_strategy}
    Functional Requirements: {functional_requirements}""",
    expected_output="""Non-functional subsystem requirements containing:
    - Performance budget allocations by subsystem
    - Quality attribute requirements with acceptance criteria
    - Measurable and testable requirement statements
    - Traceability to parent non-functional requirements
    - Verification approach recommendations""",
    agent=requirements_engineer,
    context=[strategy_development_task, functional_decomposition_task]
)
```

### Task 6: Interface Requirements Definition
```python
interface_definition_task = Task(
    description="""Define subsystem interfaces and data flows based on ICD and 
    decomposed functional requirements.
    
    Actions:
    1. Extract interface specifications from ICD and architecture
    2. Define data flows between subsystems
    3. Create interface requirement statements
    4. Specify protocols, formats, and timing constraints
    5. Ensure interface completeness and consistency
    
    Functional Requirements: {functional_requirements}
    Non-Functional Requirements: {nonfunctional_requirements}""",
    expected_output="""Interface requirements containing:
    - Complete interface specifications for each subsystem
    - Data flow diagrams and descriptions
    - Protocol and format specifications
    - Timing and performance constraints
    - Interface consistency verification""",
    agent=requirements_engineer,
    context=[functional_decomposition_task, nonfunctional_decomposition_task]
)
```

### Task 7: Traceability Matrix Creation
```python
traceability_task = Task(
    description="""Create comprehensive traceability matrices linking all parent 
    requirements to decomposed subsystem requirements.
    
    Actions:
    1. Build traceability matrix (parent to child requirements)
    2. Verify complete coverage of parent requirements
    3. Identify gaps, overlaps, or missing allocations
    4. Generate traceability reports and metrics
    5. Create change impact assessment framework
    
    All Decomposed Requirements: {all_decomposed_requirements}""",
    expected_output="""Traceability documentation containing:
    - Complete traceability matrix (parent-to-child)
    - Coverage analysis with gap identification
    - Overlap analysis and resolution recommendations
    - Traceability metrics and quality assessment
    - Change impact assessment procedures""",
    agent=quality_assurance_agent,
    context=[functional_decomposition_task, nonfunctional_decomposition_task, interface_definition_task]
)
```

### Task 8: Quality Validation and Compliance Check
```python
quality_validation_task = Task(
    description="""Validate all decomposed requirements against quality standards 
    and compliance requirements.
    
    Actions:
    1. Check requirement quality (clear, testable, unambiguous)
    2. Validate against applicable standards and best practices
    3. Verify compliance with regulatory requirements
    4. Assess requirement completeness and consistency
    5. Generate quality improvement recommendations
    
    All Requirements: {all_requirements}
    Traceability Matrix: {traceability_matrix}""",
    expected_output="""Quality assurance report containing:
    - Quality assessment for each requirement
    - Standards and regulatory compliance verification
    - Issue identification with severity ratings
    - Quality metrics and scoring
    - Improvement recommendations and action items""",
    agent=quality_assurance_agent,
    context=[traceability_task]
)
```

### Task 9: Final Documentation and Formatting
```python
documentation_task = Task(
    description="""Create professional requirement documents and deliverable packages 
    for stakeholders.
    
    Actions:
    1. Apply consistent formatting and numbering schemes
    2. Generate subsystem requirement documents
    3. Create executive summary and overview documentation
    4. Compile traceability matrices and quality reports
    5. Package all deliverables for stakeholder distribution
    
    Quality Validated Requirements: {validated_requirements}
    Traceability Documentation: {traceability_docs}
    Quality Reports: {quality_reports}""",
    expected_output="""Professional documentation package containing:
    - Formatted subsystem requirement documents
    - Executive summary with key metrics
    - Complete traceability matrices
    - Quality and compliance reports
    - Stakeholder presentation materials
    - Implementation guidance documents""",
    agent=documentation_specialist,
    context=[quality_validation_task]
)
```

## Crew Configuration

```python
# Create the streamlined crew
requirements_decomposition_crew = Crew(
    agents=[
        requirements_analyst,
        decomposition_strategist, 
        requirements_engineer,
        quality_assurance_agent,
        documentation_specialist
    ],
    tasks=[
        requirements_extraction_task,
        context_analysis_task,
        strategy_development_task,
        functional_decomposition_task,
        nonfunctional_decomposition_task,
        interface_definition_task,
        traceability_task,
        quality_validation_task,
        documentation_task
    ],
    knowledge=knowledge,
    process=Process.sequential,
    verbose=True,
    memory=True,
    cache=True,
    max_rpm=100
)
```

## Key Tools

```python
@tool
def knowledge_search_tool(query: str, doc_type: str = None) -> str:
    """Search knowledge repository with optional document type filtering"""
    metadata_filter = {"type": doc_type} if doc_type else None
    return knowledge.search(query=query, metadata_filter=metadata_filter, top_k=5)

@tool  
def requirement_extraction_tool(text: str) -> dict:
    """Extract and structure requirements from document text"""
    # Implementation for parsing requirements using NLP/patterns
    pass

@tool
def architecture_mapping_tool(requirements: list, architecture: dict) -> dict:
    """Map requirements to architectural components"""
    # Implementation for requirement-architecture mapping
    pass

@tool
def performance_allocation_tool(requirement: str, subsystems: list) -> dict:
    """Allocate performance budgets across subsystems"""
    # Implementation for performance decomposition
    pass
```

## Usage Example

```python
# Execute the streamlined decomposition workflow
result = requirements_decomposition_crew.kickoff(inputs={
    "primary_specification": "System Requirements Specification v2.1",
    "target_system": "Emergency Communication System",
    "decomposition_depth": "subsystem_level"
})

# Access deliverables
final_requirements = result.raw
structured_output = result.json_dict
```