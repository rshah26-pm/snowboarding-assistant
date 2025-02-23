import os
from groq import Groq


def get_snowboard_assistant_response(user_prompt):
    """
    Get a response from the AI snowboarding assistant using Groq.
    
    Args:
        user_prompt (str): The user's question or request
        
    Returns:
        str: The AI assistant's response
    """
    # Initialize Groq client
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    
    # Create the system context
    system_context = """You are a helpful snowboarding assistant that helps users plan their season and trips.
    You can provide advice about:
    - Resort recommendations and planning
    - Trip planning and logistics 
    - Gear recommendations and purchases
    - Clothing and accessories advice
    - General snowboarding questions
    
    Users may provide:
    - Lists of resorts they want to visit
    - Planned trips they want to take
    - Gear they're considering buying
    - Clothing items they need
    - Accessories they're interested in
    
    Help them make informed decisions about their snowboarding season planning.
    Focus on being practical and specific in your recommendations."""

    # Create the chat completion
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_context
            },
            {
                "role": "user", 
                "content": user_prompt
            }
        ],
        model="llama3-8b-8192",  # Using Llama3 model through Groq
        temperature=0.7
    )
    
    return chat_completion.choices[0].message.content

def main():
    print("Welcome to the Snowboard Trip Planner AI Assistant!")
    print("Ask me anything about planning your snowboarding season, trips, or gear.")
    
    while True:
        user_input = input("\nWhat would you like to know? (or type 'quit' to exit): ")
        
        if user_input.lower() == 'quit':
            print("Thanks for using the Snowboard Trip Planner! Have a great season!")
            break
            
        try:
            response = get_snowboard_assistant_response(user_input)
            print("\nAssistant:", response)
        except Exception as e:
            print(f"\nSorry, there was an error: {str(e)}")
            print("Please try again.")

if __name__ == "__main__":
    main()

