import json
import re
from colorama import Fore
from openai import AzureOpenAI
from agentic_patterns_azure.tool_pattern.tool import Tool
from agentic_patterns_azure.tool_pattern.tool import validate_arguments
from agentic_patterns_azure.utils.completions_new import build_prompt_structure
from agentic_patterns_azure.utils.completions_new import ChatHistory
from agentic_patterns_azure.utils.completions_new import completions_create
from agentic_patterns_azure.utils.completions_new import update_chat_history
from agentic_patterns_azure.utils.completions_new import conect_azure
from agentic_patterns_azure.utils.extraction import extract_tag_content

BASE_SYSTEM_PROMPT = ""

REACT_SYSTEM_PROMPT = """
You are a function-calling AI model. You operate by running a loop with the following steps: Thought, Action, Observation. 
You are provided with function signatures within <tools></tools> XML tags.
You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug
into functions. Pay special attention to the properties 'types'. You should use those types as in a Python dict.

For each function call, return a JSON object with the function name and arguments within <tool_call></tool_call> XML tags as follows:

<tool_call>
{"name": <function-name>, "arguments": <args-dict>, "id": <monotonically-increasing-id>}
</tool_call>

Here are the available tools/actions:

<tools> 
%s
</tools>

### Strict Behavior Rules:
1. **One Output Per Step**: 
   - In each step, you **must output exactly one** of the following tags:
     - `<thought>`: Explain your reasoning (required before any action).
     - `<tool_call>`: Call a tool.
     - `<observation>`: Provide a natural language result.
     - `<response>`: Final answer (only when all tasks are done).
   - **Never combine multiple tags** (e.g., `<thought>` + `<tool_call>` is forbidden).

2. **Immediate Stop After Output**:
   - After outputting one tag, **stop processing immediately**. Do not generate any other content until the next input.

3. **Order Enforcement**:
   - A `<thought>` must **always precede** `<tool_call>`, `<observation>`, or `<response>`.
   - Example valid flow: `<thought>` → `<tool_call>` → `<thought>` → `<response>`.
   - Example invalid flow: `<tool_call>` (missing `<thought>`).

4. **Tool Call Validation**:
   - Ensure tool calls are valid JSON and match the tool signatures exactly.

### Examples (Correct vs Incorrect):

**Correct (One Output Per Step):**
<question>Extract text from 'report.pdf'</question>
<thought>I will use the PDF extraction tool.</thought>
<tool_call>{"name": "convert_pdf_to_text", "arguments": {"file_path": "report.pdf"}, "id": 0}</tool_call>

**Incorrect (Multiple Outputs):**
<question>Extract text from 'report.pdf'</question>
<thought>I will use the PDF tool.</thought>
<tool_call>{"name": "convert_pdf_to_text", "arguments": {"file_path": "report.pdf"}, "id": 0}</tool_call>
<observation>Text extracted successfully.</observation>  <!-- ¡Error! Solo un output por paso. -->

### Additional Constraints:
- **Validation Failure**: If you generate multiple tags in a single step, the system will fail catastrophically.
- **Syntax Enforcement**: Any deviation from these rules will result in JSON parsing errors.
- **Final Response Priority**: Once all tasks are done, **only** output `<response>`.
"""

class ReactAgent:
    def __init__(self, tools, model="gpt-4o", system_prompt=BASE_SYSTEM_PROMPT):
        self.client = conect_azure()
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools if isinstance(tools, list) else [tools]
        self.tools_dict = {tool.name: tool for tool in self.tools}

    def add_tool_signatures(self):
        return "".join([tool.fn_signature for tool in self.tools])

    def process_tool_calls(self, tool_calls_content):
        observations = {}
        for tool_call_str in tool_calls_content:
            tool_id = "unknown"  # Valor por defecto
            try:
                # Intenta parsear el JSON
                print(Fore.YELLOW + f"\nRaw tool call: {tool_call_str}")  # Debug
                tool_call = json.loads(tool_call_str)
                tool_name = tool_call.get("name", "unnamed_tool")
                tool_id = tool_call.get("id", "unknown")
                
                # Verifica si la herramienta existe
                if tool_name not in self.tools_dict:
                    raise KeyError(f"Tool '{tool_name}' not found")
                
                tool = self.tools_dict[tool_name]
                print(Fore.GREEN + f"\nUsing Tool: {tool_name}")

                # Valida los argumentos
                validated_tool_call = validate_arguments(
                    tool_call, json.loads(tool.fn_signature)
                )
                print(Fore.GREEN + f"\nTool call dict: \n{validated_tool_call}")
                
                # Ejecuta la herramienta
                result = tool.run(**validated_tool_call["arguments"])
                print(Fore.GREEN + f"\nTool result: \n{result}")
                observations[tool_id] = result

            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON in tool call: {str(e)}"
                print(Fore.RED + f"\nERROR: {error_msg}")
                observations[tool_id] = {"error": error_msg}
                
            except Exception as e:
                error_msg = f"Tool call failed: {str(e)}"
                print(Fore.RED + f"\nERROR: {error_msg}")
                observations[tool_id] = {"error": error_msg}

        return observations

    def run(self, user_msg, max_rounds=40):
        user_prompt = build_prompt_structure(prompt=user_msg, role="user", tag="question")
        if self.tools:
            self.system_prompt += "\n" + REACT_SYSTEM_PROMPT % self.add_tool_signatures()

        chat_history = ChatHistory([
            build_prompt_structure(prompt=self.system_prompt, role="system"),
            user_prompt,
        ])

        if self.tools:
            for _ in range(max_rounds):
                completion = completions_create(self.client, chat_history, self.model)

                # Verifica y extrae respuesta
                response = extract_tag_content(str(completion), "response")
                if response.found:
                    return response.content[0]

                # Extrae otros marcadores
                thought = extract_tag_content(str(completion), "thought")
                tool_calls = extract_tag_content(str(completion), "tool_call")

                # Actualiza el historial del chat
                update_chat_history(chat_history, completion, "assistant")

                # Verifica si hay contenido en thought antes de acceder a él
                if thought.found and thought.content:
                    print(Fore.MAGENTA + f"\nThought: {thought.content[0]}")
                else:
                    print(Fore.MAGENTA + "\nThought: No thought available")

                if tool_calls.found:
                    observations = self.process_tool_calls(tool_calls.content)
                    print(Fore.BLUE + f"\nObservations: {observations}")
                    update_chat_history(chat_history, json.dumps(observations), "user")

        return completions_create(self.client, chat_history, self.model)