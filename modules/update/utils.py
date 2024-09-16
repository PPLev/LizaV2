import asyncio
import os
import subprocess
import sys

import httpx

from event import Event


def get_current_commit_sha(branch_name):
    """Возвращает текущий SHA коммита для указанной ветки."""
    try:
        current_commit = subprocess.check_output(
            ['git', '-C', ".", 'rev-parse', branch_name]
        ).strip().decode('utf-8')

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


def update_local_repository(repo_path, branch_name):
    """Обновляет локальный репозиторий с удалённого."""
    try:
        # Переход к директории репозитория и выполнение git pull
        subprocess.check_call(['git', '-C', repo_path, 'pull', 'origin', branch_name])
        print(f"Локальный репозиторий в '{repo_path}' обновлён до ветки '{branch_name}'")

    except subprocess.CalledProcessError as e:
        print("Ошибка при обновлении репозитория:", e)


async def updater_acceptor(queue: asyncio.Queue, config: dict):
    repo_owner = config['repo_owner']
    repo_name = config['repo_name']
    branch_name = config['branch_name']

    while True:
        await asyncio.sleep(0)
        if not queue.empty():
            event: Event = await queue.get()
            if event.purpose == "inspect":
                if check_new_commit(repo_owner, repo_name, branch_name):
                    await event.reply("Новая версия есть")
                else:
                    await event.reply("Нет новых версий")

            if event.purpose == "update":
                await event.reply("Типо обновилась")
