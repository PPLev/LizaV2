import os
import subprocess
import sys

import httpx


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
        return
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
            return current_commit_sha  # Возвращаем текущий SHA, если нет нового коммита

    else:
        print("Ошибка при обращении к GitHub API:", response.status_code)
        return None
