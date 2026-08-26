from openai import OpenAI
import os
import json


def get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_API_BASE")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    kwargs = {"api_key": api_key}

    # Only set base_url when explicitly configured.
    if base_url:
        kwargs["base_url"] = base_url

    return OpenAI(**kwargs)

def generate_press_release(brief_path: str, output_path: str):
   
    with open(brief_path, "r", encoding="utf-8") as brief_file:
        brief_content = brief_file.read()

    client = get_client()

    response = client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        temperature=0.7,
        max_tokens=200,
        messages=[
            {
                "role": "assistant",
                "content": (
                    "You are a PR specialist. Based on this product brief, write an exciting, 150-word professional press release."
                ),
            },
            {
                "role": "user",
                "content": (
                    "product brief:\n\n"
                    f"{brief_content}"
                ),
            },
        ],
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("The model returned empty code")

    with open(output_path, "w", encoding="utf-8") as out_file:
        out_file.write(content)


def analyze_press_release(pr_path: str) -> str:

    with open(pr_path, "r", encoding="utf-8") as pr_file:
        pr_content = pr_file.read()

    client = get_client()

    response = client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        temperature=0.5,
        max_tokens=200,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a cynical, skeptical tech journalist. Read the following press release. Identify the 'Top 3 Toughest Questions' a journalist would ask about this product. Return the valid raw JSON object with a single key tough_questions, which is a list of strings, no additional explanations, or markdown fences."
                ),
            },
            {
                "role": "user",
                "content": (
                    "press release:\n\n"
                    f"{pr_content}"
                ),
            },
        ],
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("The model returned an empty review")

    content = content.strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Model returned invalid JSON:\n{content}"
        ) from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("Model response is not a JSON object")

    if "tough_questions" not in parsed:
        raise RuntimeError(
            "Model response does not contain the 'tough_questions' key"
        )

    if not isinstance(parsed["tough_questions"], list):
        raise RuntimeError("'tough_questions' must be a list")

    return json.dumps(parsed, indent=2)


if __name__ == "__main__":
    generate_press_release("product_brief.txt", "press_release.txt")
    response = analyze_press_release("press_release.txt")
    print(response)
    