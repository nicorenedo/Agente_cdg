# Frontend for Template POC

This is the frontend component of the Template POC project. It is built using [Streamlit](https://streamlit.io/) to provide a user interface for interacting with an AI agent (`ReactAgent`). Below is a detailed guide to help new developers understand and work with this project.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [File Structure](#file-structure)
3. [How It Works](#how-it-works)
4. [Setup Instructions](#setup-instructions)
5. [Key Components](#key-components)
6. [Customization Guide](#customization-guide)
7. [Troubleshooting](#troubleshooting)

---

## Project Overview

The frontend allows users to:
- Enter a query to interact with the AI agent.
- Optionally upload a file (e.g., `.txt`, `.csv`, `.json`) for additional processing.
- View the agent's response directly in the UI.

The backend logic is handled by the `ReactAgent`, which uses predefined tools to process user inputs.

---

## File Structure

```
frontend/
├── src/
│   ├── app.py          # Main Streamlit application
│   └── ...             # Other frontend-related files
└── README.md           # Documentation for the frontend
```

---

## How It Works

1. **User Input**:
   - Users can enter a query in the text input box.
   - Optionally, users can upload a file for processing.

2. **Agent Interaction**:
   - The `ReactAgent` processes the query and/or file content using predefined tools (`sum_two_elements`, `multiply_two_elements`, `compute_log`).

3. **Response Display**:
   - The agent's response is displayed in the Streamlit UI.

4. **Error Handling**:
   - Errors during processing are caught and displayed as error messages.

---

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Streamlit installed (`pip install streamlit`)

### Steps
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   streamlit run src/app.py
   ```

3. Open the application in your browser at `http://localhost:8501`.

---

## Key Components

### `app.py`
- **Purpose**: Main entry point for the Streamlit application.
- **Key Features**:
  - User query input
  - File upload functionality
  - Interaction with the `ReactAgent`

### `ReactAgent`
- **Purpose**: Processes user inputs using predefined tools.
- **Tools**:
  - `sum_two_elements`: Adds two numbers.
  - `multiply_two_elements`: Multiplies two numbers.
  - `compute_log`: Computes the logarithm of a number.

---

## Customization Guide

### Adding New Tools
1. Define the new tool in the `defined_tools` module.
2. Import the tool in `app.py`.
3. Add the tool to the `ReactAgent` initialization:
   ```python
   agent = ReactAgent(tools=[existing_tool, new_tool])
   ```

### Modifying the UI
- Update the Streamlit UI elements in `app.py`:
  - Change titles, descriptions, or input fields as needed.

### Supporting Additional File Types
- Update the `type` parameter in the `st.file_uploader` function:
  ```python
  uploaded_file = st.file_uploader("Upload a file:", type=["txt", "csv", "json", "xml"])
  ```

---

## Troubleshooting

### Common Issues
1. **Module Not Found**:
   - Ensure the backend directory is correctly added to the Python path in `app.py`.

2. **File Upload Errors**:
   - Verify that the uploaded file is in a supported format.

3. **Agent Errors**:
   - Check the implementation of the `ReactAgent` and its tools.

### Debugging Tips
- Use `st.write` or `print` statements to debug issues in `app.py`.
- Check the Streamlit logs in the terminal for error details.

---

## Additional Resources
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Python Pathlib Documentation](https://docs.python.org/3/library/pathlib.html)
- [Project Backend Documentation](../backend/README.md) (if available)

---
