import os
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create client
client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

# Example API call
message = client.messages.create(
    # Uncomment the model you want to use
    # model="claude-3-5-sonnet-20240620", # Balanced performance and cost
    # model="claude-3-opus-20240229",     # Highest quality, most expensive
    model="claude-3-haiku-20240307",      # Fastest and most affordable
    max_tokens=4000,
    temperature=0.7,
    messages=[
        {
            "role": "user", 
            "content": "Edit this paragraph to be more formal and academic in tone: " +
                       "The internet lets people share stuff with each other really easily. " +
                       "This is cool because it means anyone can put their ideas out there " +
                       "without needing a lot of money or connections."
        }
    ]
)

print(message.content[0].text)