import streamlit as st
from g1 import generate_response
import json
from io import StringIO
from PIL import Image
import pytesseract
import io

def main():
    st.set_page_config(page_title="g1 prototype", page_icon="🧠", layout="wide")
    
    st.title("g1: Using Llama-3.1 70b on Groq to create o1-like reasoning chains")
    
    st.markdown("""
    This is an early prototype of using prompting to create o1-like reasoning chains to improve output accuracy. It is not perfect and accuracy has yet to be formally evaluated. It is powered by Groq so that the reasoning step is fast!
                
    Open source [repository here](https://github.com/bklieger-groq)
    """)

    image_accepted_types = ['png', 'jpg', 'jpeg']
    uploaded_file = st.file_uploader("Upload a file for additional context (optional)", type=None)  # Allow all file types
    
    file_content = None
    image_content = None
    
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        st.write(f"Uploaded file extension: {file_extension}")
        
        if file_extension in image_accepted_types:
            image = Image.open(io.BytesIO(uploaded_file.getvalue()))
            image_content = pytesseract.image_to_string(image)
            st.success(f"Image '{uploaded_file.name}' uploaded and processed successfully!")
            st.image(image, caption="Uploaded Image", width=500)
        else:
            try:
                stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                file_content = stringio.read()
                st.success(f"File '{uploaded_file.name}' uploaded and read as text successfully!")
            except UnicodeDecodeError:
                st.error("Unable to read the file as text. Please upload a text-based file or an image.")


    
    # Text input for user query
    user_query = st.text_input("Enter your query:", placeholder="e.g., How many 'R's are in the word strawberry?")
    
    if user_query:
        st.write("Generating response...")
        
        # Create empty elements to hold the generated text and total time
        response_container = st.empty()
        time_container = st.empty()
        
        # Generate and display the response
        for steps, total_thinking_time in generate_response(user_query, file_content=file_content, image_content=image_content):
            with response_container.container():
                for i, (title, content, thinking_time) in enumerate(steps):
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
                            st.markdown(content.replace('\n', '<br>'), unsafe_allow_html=True)
                    else:
                        with st.expander(title, expanded=True):
                            st.markdown(content.replace('\n', '<br>'), unsafe_allow_html=True)
            
            # Only show total time when it's available at the end
            if total_thinking_time is not None:
                time_container.markdown(f"**Total thinking time: {total_thinking_time:.2f} seconds**")

if __name__ == "__main__":
    main()
