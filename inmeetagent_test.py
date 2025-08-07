import dotenv, os
from vertexai import agent_engines

# Load environment variables from a .env file
dotenv.load_dotenv()


def invoke_inmeet_agent(user_input: str) -> str:

    agent_engine_id = "429170174646550528"

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

    # Call the function
    final_briefing = invoke_inmeet_agent("I’m not sure I understand what you just said. Can you explain again?")

    # Print the final result
    print("\n---  In-Meeting result ---")
    print(final_briefing)
    print("-" * 30)