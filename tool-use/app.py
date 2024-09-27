import streamlit as st
from g1_experimental import generate_response
import json

def main():
    st.set_page_config(page_title="g1 prototype", page_icon="🧠", layout="wide")
    
    st.title("g1: Powered by Llama on Groq producing o1-like reasoning chains and tool calling")
    
    st.markdown("""
    This is an enhanced prototype of using prompting to create o1-like reasoning chains to improve output accuracy. 
    It now includes tool calling capabilities for calculations and basic code execution. 
    It is powered by Groq for fast reasoning steps!
                
    Open source [repository here](https://github.com/bklieger-groq)
    """)
    
    # Text input for user query
    user_query = st.text_input("Enter your query:", placeholder="e.g., What's the square root of 256 plus the sine of pi/4?")
    
    if user_query:
        st.write("Generating response...")
        
        # Create empty elements to hold the generated text and total time
        response_container = st.empty()
        time_container = st.empty()
        
        # Generate and display the response
        for steps, total_thinking_time in generate_response(user_query):
            with response_container.container():
                for step in steps:
                    # Unpack step information, handling both old and new formats
                    if len(step) == 3:
                        title, content, thinking_time = step
                        tool, tool_input, tool_result = None, None, None
                    elif len(step) == 6:
                        title, content, thinking_time, tool, tool_input, tool_result = step
                    else:
                        st.error(f"Unexpected step format: {step}")
                        continue

                    # Ensure content is a string
                    if not isinstance(content, str):
                        content = json.dumps(content)
                    
                    if title.startswith("Final Answer"):
                        st.markdown(f"### {title}")
                        if '```' in content:
                            parts = content.split('```')
                            for index, part in enumerate(parts):
                                if index % 2 == 0:
                                    st.markdown(part)
                                else:
                                    if '\n' in part:
                                        lang_line, code = part.split('\n', 1)
                                        lang = lang_line.strip()
                                    else:
                                        lang = ''
                                        code = part
                                    st.code(part, language=lang)
                        else:
                            st.write(content.replace('\n', '<br>'), unsafe_allow_html=True)
                    else:
                        with st.expander(title, expanded=True):
                            st.write(content.replace('\n', '<br>'), unsafe_allow_html=True)
                            if tool:
                                st.markdown(f"**Tool Used:** {tool}")
                                st.markdown(f"**Tool Input:** `{tool_input}`")
                                st.markdown(f"**Tool Result:** {str(tool_result)[:200] + '...' if len(str(tool_result)) > 200 else tool_result}")
                    st.markdown(f"*Thinking time: {thinking_time:.2f} seconds*")
            
            # Only show total time when it's available at the end
            if total_thinking_time is not None:
                time_container.markdown(f"**Total thinking time: {total_thinking_time:.2f} seconds**")

if __name__ == "__main__":
    main()
