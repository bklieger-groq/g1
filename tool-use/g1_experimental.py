import groq
import time
import os
import json
import math
import subprocess
from exa_py import Exa
import requests

# Initialize the Groq and Exa clients
client = groq.Groq()
exa = Exa(api_key=os.environ.get("EXA_API_KEY"))

model = "llama-3.1-70b-versatile"

def make_api_call(messages, max_tokens, is_final_answer=False, custom_client=None):
    global client
    if custom_client is not None:
        client = custom_client

    for attempt in range(3):
        try:
            if is_final_answer:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.2,
                )
                return response.choices[0].message.content
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.2,
                    response_format={"type": "json_object"},
                )
                return json.loads(response.choices[0].message.content)
        except Exception as e:
            if attempt == 2:
                if is_final_answer:
                    return {
                        "title": "Error",
                        "content": f"Failed to generate final answer after 3 attempts. Error: {str(e)}",
                    }
                else:
                    return {
                        "title": "Error",
                        "content": f"Failed to generate step after 3 attempts. Error: {str(e)}",
                        "next_action": "final_answer",
                    }
            time.sleep(1)  # Wait for 1 second before retrying

def calculate(expression):
    try:
        return eval(expression, {"__builtins__": None}, {"math": math})
    except Exception as e:
        return f"Error: {str(e)}"

def wolfram_alpha_calculate(query):
    app_id = os.environ.get('WOLFRAM_APP_ID')
    if not app_id:
        return "Error: Wolfram Alpha App ID is not set in environment variables."
    
    url = 'https://api.wolframalpha.com/v2/query'
    params = {
        'appid': app_id,
        'input': query,
        'output': 'json',
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        # Check if the query was successful
        if data['queryresult']['success']:
            result = ''
            for pod in data['queryresult']['pods']:
                for subpod in pod.get('subpods', []):
                    plaintext = subpod.get('plaintext')
                    if plaintext:
                        result += f"{plaintext}\n"
            return result.strip() if result else "No plaintext result available."
        else:
            return "No results found for the query."
    except requests.Timeout:
        return "Error: The request to Wolfram Alpha timed out."
    except Exception as e:
        return f"An error occurred: {str(e)}"

def web_search(query, num_results=5):
    try:
        # Perform a neural search using Exa and retrieve up to 'num_results'
        search_results = exa.search_and_contents(
            query,
            type="auto",
            use_autoprompt=True,
            num_results=num_results,
            highlights=True,
            text=True
        )

        # Prepare formatted output from the Exa API results
        formatted_results = []
        for idx, result in enumerate(search_results.results):
            title = result.title or 'No title found'
            snippet = result.text or 'No snippet found'
            url = result.url or 'No URL found'
            id = result.id or 'No ID found'
            formatted_results.append(
                f"Result {idx + 1}:\nID: {id}\nTitle: {title}\nSnippet: {snippet}\nURL: {url}\n"
            )

        return "\n".join(formatted_results)
    except Exception as e:
        return f"An error occurred while using Exa API: {str(e)}"

def fetch_page_content(ids):
    try:
        # Fetch content of the provided IDs using Exa
        page_contents = exa.get_contents(ids, text=True)

        # Format and return the page contents
        formatted_contents = []
        for page in page_contents.results:
            title = page.title or 'No title found'
            text = page.text or 'No text found'
            formatted_contents.append(f"Title: {title}\nContent: {text}\n")

        return "\n".join(formatted_contents)
    except Exception as e:
        return f"An error occurred while retrieving page content: {str(e)}"

def execute_code(code):
    try:
        # Execute the code in a subprocess for safety
        result = subprocess.run(
            ['python3', '-c', code],
            capture_output=True,
            text=True,
            timeout=5,
            env={"PYTHONPATH": os.getcwd()}
        )
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def generate_response(prompt, custom_client=None):
    messages = [
        {
            "role": "system",
            "content": """You are an expert AI assistant that explains your reasoning step by step. For each step, provide a title that describes what you're doing in that step, along with the content. Decide if you need another step or if you're ready to give the final answer. Respond in JSON format with 'title', 'content', and 'next_action' (either 'continue' or 'final_answer') keys.

You can also use tools by including:
- A 'tool' key with one of the following values: 'code_executor', 'web_search', 'fetch_page_content', or 'wolfram_alpha'.
- A 'tool_input' key with the expression, code to execute, search query, or list of IDs.
- For 'web_search', you can specify the number of results (default is 5) by adding a 'num_results' key.
- For 'fetch_page_content', provide a list of IDs (from previous web search results) in 'tool_input'.
- When using 'wolfram_alpha', provide your query as 'tool_input'; the assistant will use the Wolfram Alpha API to compute the result.

When using 'web_search', the tool result will include IDs for each result, which you can use with 'fetch_page_content'. If you cannot find information in a website, try another one, up to 5 times.
CONFIRM ALL PREVIEW HIGHLIGHTS FROM 'web_search' by calling 'fetch_page_content' to get the most up to date information.

USE AS MANY REASONING STEPS AS POSSIBLE. AT LEAST 3. BE AWARE OF YOUR LIMITATIONS AS AN LLM AND WHAT YOU CAN AND CANNOT DO. IN YOUR REASONING, INCLUDE EXPLORATION OF ALTERNATIVE ANSWERS. CONSIDER YOU MAY BE WRONG, AND IF YOU ARE WRONG IN YOUR REASONING, WHERE IT WOULD BE. FULLY TEST ALL OTHER POSSIBILITIES. YOU CAN BE WRONG. WHEN YOU SAY YOU ARE RE-EXAMINING, ACTUALLY RE-EXAMINE, AND USE ANOTHER APPROACH TO DO SO. DO NOT JUST SAY YOU ARE RE-EXAMINING. USE AT LEAST 3 METHODS TO DERIVE THE ANSWER. USE BEST PRACTICES.

Example of a valid JSON response:
```json
{
    "title": "Using Wolfram Alpha to Calculate",
    "content": "I'll use Wolfram Alpha to compute the integral of sin(x).",
    "tool": "wolfram_alpha",
    "tool_input": "integrate sin(x)",
    "next_action": "continue"
}```
""",
        },
        {"role": "user", "content": prompt},
        {
            "role": "assistant",
            "content": "Thank you! I will now think step by step following my instructions, starting at the beginning after decomposing the problem.",
        },
    ]

    steps = []
    step_count = 1
    total_thinking_time = 0

    while True:
        start_time = time.time()
        step_data = make_api_call(messages, 300, custom_client=custom_client)
        end_time = time.time()
        thinking_time = end_time - start_time
        total_thinking_time += thinking_time

        if 'tool' in step_data:
            if step_data['tool'] == 'calculator':
                tool_result = calculate(step_data['tool_input'])
            elif step_data['tool'] == 'code_executor':
                tool_result = execute_code(step_data['tool_input'])
            elif step_data['tool'] == 'web_search':
                num_results = step_data.get('num_results', 5)
                tool_result = web_search(step_data['tool_input'], num_results)
            elif step_data['tool'] == 'fetch_page_content':
                ids = step_data['tool_input']
                if not isinstance(ids, list):
                    ids = [ids]
                tool_result = fetch_page_content(ids)
            elif step_data['tool'] == 'wolfram_alpha':
                tool_result = wolfram_alpha_calculate(step_data['tool_input'])
            else:
                tool_result = f"Error: Unknown tool '{step_data['tool']}'"
            step_data['tool_result'] = tool_result

        steps.append(
            (
                f"Step {step_count}: {step_data['title']}",
                step_data['content'],
                thinking_time,
                step_data.get('tool'),
                step_data.get('tool_input'),
                step_data.get('tool_result')
            )
        )

        messages.append({"role": "assistant", "content": json.dumps(step_data)})
        if 'tool_result' in step_data:
            messages.append(
                {"role": "system", "content": f"Tool result: {step_data['tool_result']}"}
            )

        if step_data['next_action'] == 'final_answer' or step_count > 25:
            break

        step_count += 1

        # Yield after each step if needed
        yield steps, None  # Uncomment if using a generator

    # Generate final answer
    messages.append(
        {
            "role": "user",
            "content": "Please provide the final answer based solely on your reasoning above. Do not use JSON formatting. Only provide the text response without any titles or preambles. Retain any formatting as instructed by the original prompt, such as exact formatting for free response or multiple choice. If you are providing a number, provide a formatted version after the raw one.",
        }
    )

    start_time = time.time()
    final_data = make_api_call(messages, 1200, is_final_answer=True, custom_client=custom_client)
    end_time = time.time()
    thinking_time = end_time - start_time
    total_thinking_time += thinking_time

    steps.append(("Final Answer", final_data, thinking_time))

    # Return the steps and total thinking time
    yield steps, total_thinking_time
