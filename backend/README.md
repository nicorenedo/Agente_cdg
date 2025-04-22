# Backend for Template POC

This is the backend component of the Template POC project. It contains the implementation of the `ReactAgent`, which follows a planning pattern to process user queries and optionally uploaded files. Below is a detailed guide to help new developers understand and work with this project.

---

## Table of Contents
1. [Overview](#overview)
2. [How the Planning Pattern Agent Works](#how-the-planning-pattern-agent-works)
3. [File Structure](#file-structure)
4. [Setup Instructions](#setup-instructions)
5. [Key Components](#key-components)
6. [Customization Guide](#customization-guide)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The backend is responsible for:
- Implementing the `ReactAgent`, which processes user inputs using a planning pattern.
- Defining tools that the agent can use to perform specific tasks (e.g., mathematical operations, file processing).

The backend is designed to be modular, allowing developers to easily add new tools or modify the agent's behavior.

---

## How the Planning Pattern Agent Works

The `ReactAgent` follows a planning pattern, which involves:
1. **Tool Initialization**:
   - The agent is initialized with a list of tools, each of which performs a specific task.
2. **Input Processing**:
   - The agent receives a user query and optionally file content.
3. **Tool Selection**:
   - Based on the input, the agent selects the appropriate tool(s) to process the query.
4. **Execution**:
   - The selected tool(s) are executed, and their results are combined to generate a response.
5. **Response Generation**:
   - The agent returns the final response to the frontend.

---

## File Structure

```
backend/
├── src/
│   ├── agentic_patterns_azure/
│   │   ├── planning_pattern/
│   │   │   └── react_agent.py   # Implementation of the ReactAgent
│   │   └── ...                  # Other agentic pattern modules
│   ├── defined_tools.py         # Tools used by the ReactAgent
│   └── ...                      # Other backend-related files
└── README.md                    # Documentation for the backend
```

---

## Setup Instructions

### Prerequisites
- Python 3.8 or higher

### Steps
1. Navigate to the backend directory:
   ```bash
   cd template_POC/backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure the backend is correctly referenced in the frontend:
   - The backend directory should be added to the Python path in the frontend's `app.py`.

---

## Key Components

### `react_agent.py`
- **Purpose**: Implements the `ReactAgent` class, which processes user inputs using a planning pattern.
- **Key Methods**:
  - `__init__`: Initializes the agent with a list of tools.
  - `run`: Processes the user query and optionally file content, selecting and executing the appropriate tools.

### `defined_tools.py`
- **Purpose**: Contains the tools used by the `ReactAgent`.
- **Example Tools**:
  - `sum_two_elements`: Adds two numbers.
  - `multiply_two_elements`: Multiplies two numbers.
  - `compute_log`: Computes the logarithm of a number.

---

## Customization Guide

### Adding New Tools
1. Define the new tool in `defined_tools.py`:
   ```python
   def new_tool(input_data):
       # Tool logic here
       return result
   ```

2. Import the tool in `react_agent.py` or wherever the agent is initialized.

3. Add the tool to the agent's initialization:
   ```python
   agent = ReactAgent(tools=[existing_tool, new_tool])
   ```

### Modifying the Agent Logic
- Update the `run` method in `react_agent.py` to change how the agent processes inputs or selects tools.

### Supporting Additional Input Types
- Modify the `run` method to handle new input types (e.g., XML files, images).

---

## Troubleshooting

### Common Issues
1. **Tool Not Found**:
   - Ensure the tool is correctly defined and imported in `react_agent.py`.

2. **Agent Errors**:
   - Check the `run` method for logic errors or missing tool implementations.

3. **File Processing Issues**:
   - Verify that the file content is correctly read and passed to the agent.

### Debugging Tips
- Add logging statements in `react_agent.py` to trace the agent's execution flow.
- Use unit tests to validate the behavior of individual tools and the agent.

---

## Additional Resources
- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Project Frontend Documentation](../frontend/README.md)

---
