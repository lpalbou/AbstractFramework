from abstractcore import create_llm

# Local
llm = create_llm("ollama", model="cogito:3b")

# Or cloud
# llm = create_llm("openai", model="gpt-4o")
# llm = create_llm("anthropic", model="claude-3-5-sonnet-latest")

response = llm.generate("What is durable execution?")
print(response.content)
