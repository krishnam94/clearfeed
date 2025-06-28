import openai
import os
PROMPT_PATH = os.path.join(os.path.dirname(__file__), '../prompts/summary_prompt.txt')

def load_prompt():
    with open(PROMPT_PATH, 'r') as f:
        return f.read()

def summarize_article(text):
    prompt = load_prompt().replace('[ARTICLE TEXT HERE]', text[:4000])
    # Replace with your OpenAI API key
    openai.api_key = os.environ.get('OPENAI_API_KEY', 'sk-...')
    try:
        response = openai.ChatCompletion.create(
            model='gpt-4o',
            messages=[{"role": "system", "content": prompt}],
            max_tokens=300
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"[Summary unavailable: {e}]"
