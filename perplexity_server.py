import os
import json
import asyncio
import aiohttp
from flask import Flask, request, jsonify

app = Flask(__name__)

# TODO: 프롬프트 엔지니어링 관련 주석 수정 필요
# PROMPT_TEMPLATES = {
#     "default": [{"role": "system", "content": "Be precise and concise."}],
#     "concise_summary": [{"role": "system", "content": "Summarize this in 3 concise bullet points."}],
#     "detailed_answer": [{"role": "system", "content": "Provide a thorough and comprehensive explanation."}],
#     "clarifying_question": [{"role": "system", "content": "Convert this into a clarifying question."}]
# }

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


# async def call_perplexity_api(query: str, recency: str, prompt_type: str) -> str:
async def call_perplexity_api(query: str, recency: str) -> str:
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return "PERPLEXITY_API_KEY is not set."

    model = os.getenv("PERPLEXITY_MODEL", "sonar")
    
    # prompt = PROMPT_TEMPLATES.get(prompt_type, PROMPT_TEMPLATES["default"]).copy()
    # prompt.append({"role": "user", "content": query})

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Be precise and concise."},
            {"role": "user", "content": query},
        ],
        "max_tokens": "512",
        "temperature": 0.2,
        "top_p": 0.9,
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": recency,
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1,
        "return_citations": True,
        "search_context_size": "low",
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(PERPLEXITY_API_URL, json=payload, headers=headers) as response:
            if response.status != 200:
                return f"Error: {response.status} - {await response.text()}"
            data = await response.json()
            content = data["choices"][0]["message"]["content"]
            if "citations" in data:
                citations = data["citations"]
                formatted_citations = "\n\nCitations:\n" + "\n".join(f"[{i+1}] {url}" for i, url in enumerate(citations))
                return content + formatted_citations
            return content


@app.route("/api/perplexity/search", methods=["POST"])
def search():
    body = request.get_json()
    query = body.get("query")
    recency = body.get("recency", "month")
    # prompt_type = body.get("prompt_type", "default")

    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    # result = asyncio.run(call_perplexity_api(query, recency, prompt_type))
    result = asyncio.run(call_perplexity_api(query, recency))
    return jsonify({"result": result})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "Perplexity API Flask server running"
    })


if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 5050))
    app.run(host="0.0.0.0", port=port)
