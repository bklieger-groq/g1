import json
import requests
import groq
import time

class OllamaHandler:
    def __init__(self, url, model):
        self.url = url
        self.model = model

    def make_api_call(self, messages, max_tokens, is_final_answer=False):
        for attempt in range(3):
            try:
                response = requests.post(
                    f"{self.url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": 0.2
                        }
                    }
                )
                response.raise_for_status()
                return json.loads(response.json()["message"]["content"])
            except Exception as e:
                if attempt == 2:
                    return self._error_response(str(e), is_final_answer)
                time.sleep(1)

    def _error_response(self, error_msg, is_final_answer):
        if is_final_answer:
            return {"title": "Error", "content": f"Failed to generate final answer after 3 attempts. Error: {error_msg}"}
        else:
            return {"title": "Error", "content": f"Failed to generate step after 3 attempts. Error: {error_msg}", "next_action": "final_answer"}

class PerplexityHandler:
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model

    def make_api_call(self, messages, max_tokens, is_final_answer=False):

        # Quick dirty fix for API calls in perplexity that removes the assistant message
        #messages[0]["content"] = messages[0]["content"] + " You will always respond ONLY with JSON with the following format: {'title': 'Title of the step', 'content': 'Content of the step', 'next_action': 'continue' or 'final_answer'}. You are not allowed to respond with anything else or any additional text. "
        if not is_final_answer:
            for i in range(len(messages)):
                if messages[i]["role"] == "assistant":
                    messages.pop(i)     

        for attempt in range(3):
            try:
                url = "https://api.perplexity.ai/chat/completions"
                payload = {"model": self.model, "messages": messages}
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                response = requests.post(url, json=payload, headers=headers)
                
                # Add specific handling for 400 error
                if response.status_code == 400:
                    error_content = response.json()
                    print(f"HTTP 400 Error: {error_content}")
                    return self._error_response(f"HTTP 400 Error: {error_content}", is_final_answer)
                
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                print("Content: ", content)
                return json.loads(content)
            except json.JSONDecodeError:
                print("Warning: content is not a valid JSON, returning raw response")
                # Better detection of final answer in the raw response for Perplexity
                forced_final_answer = False
                if '"next_action": "final_answer"' in content.lower().strip():
                    forced_final_answer = True
                print("Forced final answer: ", forced_final_answer)
                
                return {
                    "title": "Raw Response",
                    "content": content,
                    "next_action": "final_answer" if (is_final_answer|forced_final_answer) else "continue"
                }
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                if attempt == 2:
                    return self._error_response(str(e), is_final_answer)
                time.sleep(1)

    def _error_response(self, error_msg, is_final_answer):
        return {
            "title": "Error",
            "content": f"API request failed after 3 attempts. Error: {error_msg}",
            "next_action": "final_answer",
        }

class GroqHandler:
    def __init__(self):
        self.client = groq.Groq()

    def make_api_call(self, messages, max_tokens, is_final_answer=False):
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                if attempt == 2:
                    return self._error_response(str(e), is_final_answer)
                time.sleep(1)

    def _error_response(self, error_msg, is_final_answer):
        if is_final_answer:
            return {"title": "Error", "content": f"Failed to generate final answer after 3 attempts. Error: {error_msg}"}
        else:
            return {"title": "Error", "content": f"Failed to generate step after 3 attempts. Error: {error_msg}", "next_action": "final_answer"}