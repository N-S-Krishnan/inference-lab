import os
from dotenv import load_dotenv
from anthropic import Anthropic


# Load environment variables from .env file
load_dotenv()

# Initialize the official client
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def run_agent_loop(prompt:str):
    print(f"🤖 Task assigned: '{prompt}'\n")

    response = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=300,
        system="You are a helpful coding assistant.",
        messages=[{"role": "user", "content": prompt}]
    )

    for block in response.content:
        if block.type == "text":
            print(f"Claude: {block.text}")

    print("\n" + "="*30)
    print("📊 USAGE")
    print(f"   Input Tokens:  {response.usage.input_tokens}")
    print(f"   Output Tokens: {response.usage.output_tokens}")
    print("="*30)

if __name__ == "__main__":
    user_prompt = "Say hello in one sentence, then explain what a token is in one sentence."
    run_agent_loop(user_prompt)
