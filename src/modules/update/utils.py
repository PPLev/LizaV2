import asyncio
import logging
import os
import subprocess
import sys

import httpx

from event import Event

logger = logging.getLogger(__name__)


def get_current_commit_sha(branch_name):
    """Возвращает текущий SHA коммита для указанной ветки."""
    try:
        current_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"]
        ).strip().decode("utf-8")

        return current_commit

    except Exception as e:
        print("Ошибка при получении текущего коммита:", e)
        return None


async def check_new_commit(repo_owner, repo_name, branch_name):
    """Проверяет, есть ли новый коммит в репозитории."""
    current_commit_sha = get_current_commit_sha(branch_name)
    if current_commit_sha is None:
        return False
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{branch_name}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url=url)

    if response.status_code == 200:
        latest_commit = response.json()
        latest_commit_sha = latest_commit['sha']
        if latest_commit_sha != current_commit_sha:
            print("Есть новый коммит!", latest_commit_sha)
            return latest_commit_sha  # Возвращаем SHA нового коммита

        else:
            print("Коммитов нет, это последний коммит.", current_commit_sha)
            return False

    else:
        print("Ошибка при обращении к GitHub API:", response.status_code)
        return False


def update_local_repository(branch_name):
    """Обновляет локальный репозиторий с удалённого."""


async def updater_acceptor(queue: asyncio.Queue, config: dict):
    repo_owner = config['repo_owner']
    repo_name = config['repo_name']
    branch_name = config['branch_name']
    autoreload = config['autoreload']

    while True:
        await asyncio.sleep(0)
        if not queue.empty():
            event: Event = await queue.get()
            if event.purpose == "inspect":
                if await check_new_commit(repo_owner, repo_name, branch_name):
                    await event.reply("Новая версия есть")
                else:
                    await event.reply("Нет новых версий")

            if event.purpose == "update":
                try:
                    subprocess.check_call(["git", "pull"])
                    if autoreload:
                        await event.reply("Обновлено до последнего коммита! Перезагружаюсь")
                        await asyncio.sleep(2)
                        # TODO: м.б. поменять на модуль перезагрузки
                        os.execv(sys.executable, [sys.executable] + sys.argv)

                    else:
                        await event.reply("Обновлено до последнего коммита! Не забудь запустить перезагрузку")

                except subprocess.CalledProcessError as e:
                    logger.error(f"Ошибка при обновлении репозитория: {e}", exc_info=True)
                    await event.reply("Ошибка при обновлении репозитория")
