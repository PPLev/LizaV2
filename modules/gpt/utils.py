from dataclasses import dataclass
from datetime import datetime
from typing import List

import httpx
import logging

from event import Event


#logger = logging.getLogger(__name__)


@dataclass
class GPTConfig:
    url: str
    token: str
    sys_prompt: str


gpt_config: GPTConfig = None


async def gpt_req(prompt):
    global gpt_config
    data = {
        "messages": [
            {"role": "system", "content": gpt_config.sys_prompt},
            {"role": "user", "content": prompt}
        ]
    }
    # if self.model:
    #     data.update({"model": self.model})

    headers = {"Content-Type": "application/json"}
    if gpt_config.token:
        headers.update({"Authorization": f"Bearer {gpt_config.token}"})

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{gpt_config.url}/chat/completions", json=data, timeout=50)

    gpt_answer = response.json()['choices'][0]['message']['content']
    return gpt_answer


async def ask_gpt(event: Event, prompt: str = "", context: List[str] = None) -> Event:
    context_items = {
        "%date%": lambda: datetime.now().strftime("%B %d, %Y"),
        "%time%": lambda: datetime.now().strftime("%H:%M:%S"),
        "%event_value%": lambda: event.value,
        # TODO: Добавить больше переменных контекста
    }

    for context_item, getter in context_items.items():
        prompt = prompt.replace(context_item, getter())

    event.value = await gpt_req(prompt)
    return event


async def init(openai_base: str, token: str, sys_prompt: str):
    global gpt_config
    if gpt_config is None:
        gpt_config = GPTConfig(url=openai_base, token=token, sys_prompt=sys_prompt)