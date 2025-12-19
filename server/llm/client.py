import os
import requests

GMS_API_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"

def call_gpt41_mini(system_prompt: str, user_text: str, image_url: str) -> str:
    api_key = os.getenv("GMS_KEY")
    if not api_key:
        raise RuntimeError("환경변수 GMS_KEY가 설정되어 있지 않습니다.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": "gpt-4.1-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
        "temperature": 0.2,
        "max_tokens": 512,
    }

    # timeout -> 서버가 멈추는 상황 방지
    r = requests.post(GMS_API_URL, headers=headers, json=payload, timeout=60)
    # r.raise_for_status()
    if r.status_code >= 400:
        raise RuntimeError(f"GMS error {r.status_code}: {r.text}")

    data = r.json()
    return data["choices"][0]["message"]["content"]