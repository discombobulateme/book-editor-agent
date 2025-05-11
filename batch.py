import os
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create client
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

# Example batch request
message_batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": "academic-paragraph-edit",
            "params": {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 4000,
                "temperature": 0.7,
                "messages": [
                    {
                        "role": "user",
                        "content": "Edit this paragraph to be more formal and academic in tone: " +
                                  "The internet lets people share stuff with each other really easily. " +
                                  "This is cool because it means anyone can put their ideas out there " +
                                  "without needing a lot of money or connections."
                    }
                ],
            },
        },
        {
            "custom_id": "technical-explanation-edit",
            "params": {
                "model": "claude-3-5-sonnet-20240620",
                "max_tokens": 8000,
                "temperature": 0.7,
                "messages": [
                    {
                        "role": "user",
                        "content": "Edit this technical explanation to be more precise and clear: " +
                                  "Open source is when you let people see the code and stuff. " +
                                  "It's important because then people can fix things if they're broken " +
                                  "and add cool new features without asking permission first."
                    }
                ],
            },
        },
    ]
)

print(message_batch)