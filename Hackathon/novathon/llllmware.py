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
    model_name = "llama3.2:latest"
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
    model = model_catalog.load_model(model_name)
    response = model.inference(f"""Provide a clear, concise summary of the following case PDF text for Kerala Police:

Summary Guidelines:
Explain the key issue or incident in simple terms.
Highlight the main facts, evidence, or processes relevant to the case.
Use language that would be clear and professional for Kerala Police personnel.
Keep the summary between 3-5 sentences long.
Include any fundamental principles, key findings, or conclusions crucial for understanding the case.
Context to Summarize:
{context}""")
    
    return response


