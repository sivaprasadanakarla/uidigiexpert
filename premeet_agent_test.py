import dotenv, os
from vertexai import agent_engines

# Load environment variables from a .env file
dotenv.load_dotenv()


def invoke_premeet_agent(client_name: str) -> str:
    """
    Invokes the pre-meeting agent to get a briefing for a specific client.

    Args:
        client_name (str): The name of the client to prepare for (e.g., "emily sheltion").

    Returns:
        str: The final, main response from the agent as a formatted string,
             or an error message if the agent fails.
    """
    agent_engine_id = "5929191219572768768"
    user_input = f"prepare me for a meeting with {client_name}"

    try:
        # Get the agent engine and create a new session
        agent_engine = agent_engines.get(agent_engine_id)
        session = agent_engine.create_session(user_id="new_user")

        # Initialize a variable to hold the last event
        last_event = None

        # Stream the query and capture each event, keeping only the last one
        for event in agent_engine.stream_query(
                user_id="new_user",
                session_id=session["id"],
                message=user_input
        ):
            print("Received event:", event)  # Optional: for debugging
            last_event = event

        # The main response is in the 'text' part of the last event's 'content'
        if last_event and 'content' in last_event and 'parts' in last_event['content']:
            main_response = last_event['content']['parts'][0]['text']
            return main_response
        else:
            return "Could not find the main response in the agent's output."

    except Exception as e:
        return f"An error occurred while invoking the agent: {e}"


if __name__ == "__main__":
    # Define the client name to test
    client_to_prepare_for = "Emily White"

    print(f"Invoking agent for: {client_to_prepare_for}...")

    # Call the function
    final_briefing = invoke_premeet_agent(client_to_prepare_for)

    # Print the final result
    print("\n--- Final Pre-Meeting Briefing ---")
    print(final_briefing)
    print("-" * 30)