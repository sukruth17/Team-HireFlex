from llmware.models import ModelCatalog

def interact_with_model(context):
    """
    Registers a predefined Ollama model, confirms its registration, and performs inference on a question.
    
    Parameters:
        question (str): The query for which inference is required.
    
    Returns:
        str: The response from the model.
    """
    # Predefined model details
    model_name = "llama2-uncensored:7b"
    model_type = "chat"
    host = "localhost"
    port = 11434
    temperature = 0

    # Register the model
    model_catalog = ModelCatalog()
    model_catalog.register_ollama_model(
        model_name=model_name,
        model_type=model_type,
        host=host,
        port=port,
        temperature=temperature
    )
    
    # Confirm the model registration
    model_card = model_catalog.lookup_model_card(model_name)
   
    
    # Load the model and perform inference
    print(context)
    model = model_catalog.load_model(model_name)
    response = model.inference(f"""Summarize the given FIR crime details

Context: {context}

Instructions: Provide only the summary. Ensure the sentence is concise, clear, and accurately reflects the key details of the FIR crime""")
    
    return response


