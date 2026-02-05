import ollama
import os

def extract_document_info(input_path):
    # if not os.path.exists(input_path):
    #     return f"Error: Document not found at {input_path}"

    # with open(input_path, 'r', encoding = 'utf-8') as file:
    #     context = file.read()
    context = str(input_path)
    
    # define system prompt
    system_instruction = (
        "You are an information extraction assistant. "
        "You task is to analyze the provided document context and extract specific details. "
        "Output the result strcitly in JSON format with these keys: "
        "'document_name', 'creation_location', 'signatories', 'summary'. "
    )
    
    # define user prompt
    user_prompt = f"Document Context: {context}\n\nBased on the text above, extract the name of the document, where it was created, and who signed it."
    
    try:
        response = ollama.chat(
            model = 'sailor2:1b',
            messages = [
                {'role': 'system', 'content': system_instruction},
                {'role': 'user', 'content': user_prompt},
            ],
            options = {
                'temperature': 0.1,
            }
        )
        return response['messages']['content']
    
    except Exception as e:
        return f"Error: {str(e)}"
    