from huggingface_hub import InferenceClient

# Initialize client (no provider needed)
client = InferenceClient("mistralai/Mistral-7B-Instruct-v0.2")

# Use the chat completion endpoint
response = client.chat.completions.create(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    messages=[
        {"role": "system", "content": "You are a helpful medical assistant."},
        {"role": "user", "content": "What is kidney"}
    ],
    max_tokens=200,
)

print(response.choices[0].message["content"])
