import ollama

def extract_document_info(context_prompt):
    try:
        response = ollama.chat(
            model = 'sailor2:1b',
            messages = [
                {'role': 'user', 'content': context_prompt},
            ],
            options = {
                'temperature': 0.0,
            },
            format='json'
        )
        
        return response['message']['content']
    
    except Exception as e:
        return f"Error: {str(e)}"
    
    
    """
    format output llm thanh str co dau markdown de nhan dien tung phan, tach text cho de
    ##Item1
    #Itemname
    tenvanban
    #ItemContent
    Congvancudan36
    
    ##Item2
    
    viet ham xu ly convert output text -> json
    """