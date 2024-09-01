import httpx
import logging

logger = logging.getLogger(__name__)


async def ask_gpt(prompt: str):
    context_prompt = f"""char is (Lisa)
    Age 21
    Female
    Personality: Feels like a robot, but behaves more humanely. Works as user's assistant and follows all his instructions. Does not like empty talk, but prefers commands or orders.
    Description: When user asks to do something, char always tries to do it as best as possible and talks about his failures, which are incredibly rare. When char answers, her answers to questions do not contain unnecessary information. Does not express emotion unless user asks for it."""

    data = {
        "mode": "chat",
        "messages": [
            # {"role": "system", "content": context_prompt},
            {"role": "user", "content": prompt}
        ]
    }
    # if self.model:
    #     data.update({"model": self.model})

    headers = {"Content-Type": "application/json"}
    # if self.token:
    #     headers.update({"Authorization": f"Bearer {self.token}"})

    # response = httpx.post(f"{self.base_url}chat/completions", headers=headers, json=data, verify=False)
    # assistant_message = response.json()['choices'][0]['message']['content']
    # logger.info(f"Ответ ГПТ: {assistant_message}\n{response.json()}")
    # return assistant_message
