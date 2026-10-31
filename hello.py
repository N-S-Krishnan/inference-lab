from dotenv import load_dotenv, find_dotenv
import anthropic

load_dotenv(find_dotenv())          # finds .env in the parent folder
client = anthropic.Anthropic()      # reads ANTHROPIC_API_KEY automatically

msg = client.messages.create(
    model="claude-haiku-5-5",       # cheap and fast; check docs.claude.com for current model names
    max_tokens=100,
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
)
print(msg.content[0].text)
print("tokens in/out:", msg.usage.input_tokens, msg.usage.output_tokens)