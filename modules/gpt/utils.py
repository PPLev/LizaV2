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
    model: str


gpt_config: GPTConfig = None


async def gpt_req(prompt, sys_prompt):
    global gpt_config
    data = {
        "messages": [
            {"role": "system", "content": sys_prompt or gpt_config.sys_prompt},
            {"role": "user", "content": prompt}
        ]
    }
    if gpt_config.model:
        data.update({"model": gpt_config.model})

    headers = {"Content-Type": "application/json"}
    if gpt_config.token:
        headers.update({"Authorization": f"Bearer {gpt_config.token}"})

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{gpt_config.url}/chat/completions", json=data, timeout=60, headers=headers)

    gpt_answer = response.json()['choices'][0]['message']['content']
    return gpt_answer


async def ask_gpt(event: Event, prompt: str = "", sys_prompt: str = None) -> Event:
    context_items = {
        "%date%": lambda: datetime.now().strftime("%B %d, %Y"),
        "%time%": lambda: datetime.now().strftime("%H:%M:%S"),
        "%event_value%": lambda: event.value,
        # TODO: Добавить больше переменных контекста
    }

    for context_item, getter in context_items.items():
        prompt = prompt.replace(context_item, getter())

    event.value = await gpt_req(prompt, sys_prompt)
    return event


async def init(config):
    global gpt_config

    openai_base = config["openai_base"]
    token = config["token"]
    sys_prompt = config["sys_prompt"]
    model = config["model"]

    if gpt_config is None:
        gpt_config = GPTConfig(url=openai_base, token=token, sys_prompt=sys_prompt, model=model)
