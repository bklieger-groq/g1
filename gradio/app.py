import gradio as gr
import os
import json
import time
import groq
from ..g1 import generate_response

def format_steps(steps, total_time):
    md_content = ""
    for title, content, thinking_time in steps:
        if title == "Final Answer":
            md_content += f"### {title}\n"
            md_content += f"{content}\n"
        else:
            md_content += f"#### {title}\n"
            md_content += f"{content}\n"
            md_content += f"_Thinking time for this step: {thinking_time:.2f} seconds_\n"
            md_content += "\n---\n"
    if total_time!=0:
        md_content += f"\n**Total thinking time: {total_time:.2f} seconds**"
    return md_content

def main(api_key, user_query):
    if not api_key:
        yield "Please enter your Groq API key to proceed."
        return
    
    if not user_query:
        yield "Please enter a query to get started."
        return
    
    try:
        # Initialize the Groq client with the provided API key
        client = groq.Groq(api_key=api_key)
    except Exception as e:
        yield f"Failed to initialize Groq client. Error: {str(e)}"
        return
    
    try:
        for steps, total_time in generate_response(user_query, custom_client=client):
            formatted_steps = format_steps(steps, total_time if total_time is not None else 0)
            yield formatted_steps
    except Exception as e:
        yield f"An error occurred during processing. Error: {str(e)}"
        return

# Define the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# 🧠 g1: Using Llama-3.1 70b on Groq to Create O1-like Reasoning Chains")
    
    gr.Markdown("""
    This is an early prototype of using prompting to create O1-like reasoning chains to improve output accuracy. It is not perfect and accuracy has yet to be formally evaluated. It is powered by Groq so that the reasoning step is fast!
    
    Open source [repository here](https://github.com/bklieger-groq)
    """)
    
    with gr.Row():
        with gr.Column():
            api_input = gr.Textbox(
                label="Enter your Groq API Key:",
                placeholder="Your Groq API Key",
                type="password"
            )
            user_input = gr.Textbox(
                label="Enter your query:",
                placeholder="e.g., How many 'R's are in the word strawberry?",
                lines=2
            )
            submit_btn = gr.Button("Generate Response")
            gr.Markdown("\n")
    
    with gr.Row():
        with gr.Column():
            output_md = gr.Markdown()
    
    submit_btn.click(fn=main, inputs=[api_input, user_input], outputs=output_md)

# Launch the Gradio app
if __name__ == "__main__":
    demo.launch()
