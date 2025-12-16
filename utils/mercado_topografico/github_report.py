import os
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple

import httpx
from dotenv import load_dotenv

load_dotenv()


class GitHubReportError(Exception):
    pass


def _parse_repo_path_from_url(raw: str) -> str:
    # Remove possíveis textos extras após a URL (como nomes soltos no comando do Discord)
    token = raw.split()[0]
    if "github.com/" not in token:
        raise GitHubReportError(f"Entrada de repositório inválida: {raw}")

    parts = token.rstrip("/").split("github.com/")
    if len(parts) != 2 or not parts[1]:
        raise GitHubReportError(f"URL de repositório inválida: {raw}")

    path = parts[1]
    if path.endswith(".git"):
        path = path[:-4]
    return path


def _iso(dt: date) -> str:
    return datetime(dt.year, dt.month, dt.day).isoformat() + "Z"


def _increment(mapping: Dict[str, int], key: str, value: int = 1) -> None:
    mapping[key] = mapping.get(key, 0) + value


async def get_github_report(
    repo_urls: List[str], start_date: date, end_date: date
) -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubReportError("GITHUB_TOKEN não configurado nas variáveis de ambiente")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    since = _iso(start_date)
    until = _iso(end_date)

    total_prs_merged = 0
    total_commits = 0

    # Agregações
    prs_by_month: Dict[str, int] = {}
    commits_by_month: Dict[str, int] = {}
    prs_by_repo: Dict[str, int] = {}
    commits_by_repo: Dict[str, int] = {}

    # Dev destaque
    prs_by_author: Dict[str, int] = {}
    commits_by_author: Dict[str, int] = {}

    # Tarefa mais longa (PR com maior lead time)
    longest_pr: Optional[Dict[str, object]] = None

    repo_details_lines = []
    misc_messages = []

    async with httpx.AsyncClient(timeout=30) as client:
        for raw_url in repo_urls:
            try:
                repo_path = _parse_repo_path_from_url(raw_url)
            except GitHubReportError as e:
                misc_messages.append(str(e))
                continue

            # Descobrir branch padrão do repositório
            repo_url = f"https://api.github.com/repos/{repo_path}"
            repo_resp = await client.get(repo_url, headers=headers)
            if repo_resp.status_code == 404:
                misc_messages.append(
                    f"Repositório não encontrado ou sem acesso: {repo_path} (HTTP 404)"
                )
                continue
            if repo_resp.status_code != 200:
                raise GitHubReportError(
                    f"Erro ao buscar dados do repositório {repo_path}: {repo_resp.status_code} {repo_resp.text}"
                )
            repo_data = repo_resp.json()
            default_branch = repo_data.get("default_branch", "main")

            # PRs mergeados no período na branch padrão
            prs_merged_count = 0
            pulls_url = f"https://api.github.com/repos/{repo_path}/pulls"
            page = 1
            while True:
                params = {
                    "state": "closed",
                    "base": default_branch,
                    "per_page": 100,
                    "page": page,
                }
                resp = await client.get(pulls_url, headers=headers, params=params)
                if resp.status_code != 200:
                    raise GitHubReportError(
                        f"Erro ao buscar PRs em {repo_path}: {resp.status_code} {resp.text}"
                    )
                pulls = resp.json()
                if not pulls:
                    break

                for pr in pulls:
                    merged_at = pr.get("merged_at")
                    if not merged_at:
                        continue
                    merged_dt = datetime.fromisoformat(
                        merged_at.replace("Z", "+00:00")
                    )
                    merged_date = merged_dt.date()
                    if not (start_date <= merged_date <= end_date):
                        continue

                    created_at = pr.get("created_at")
                    pr_number = pr.get("number")
                    pr_title = pr.get("title") or ""
                    user = pr.get("user") or {}
                    author_login = user.get("login") or "Desconhecido"

                    prs_merged_count += 1
                    month_key = merged_date.strftime("%Y-%m")
                    _increment(prs_by_month, month_key)
                    _increment(prs_by_repo, repo_path)
                    _increment(prs_by_author, author_login)

                    # Tarefa mais longa: diferença entre criação e merge do PR
                    if created_at:
                        created_dt = datetime.fromisoformat(
                            created_at.replace("Z", "+00:00")
                        )
                        lead_time = merged_dt - created_dt
                        if (
                            longest_pr is None
                            or lead_time > longest_pr["lead_time"]  # type: ignore[index]
                        ):
                            longest_pr = {
                                "repo": repo_path,
                                "number": pr_number,
                                "title": pr_title,
                                "author": author_login,
                                "created_at": created_dt,
                                "merged_at": merged_dt,
                                "lead_time": lead_time,
                            }

                if len(pulls) < 100:
                    break
                page += 1

            total_prs_merged += prs_merged_count

            # Commits na branch padrão no período
            commits_url = f"https://api.github.com/repos/{repo_path}/commits"
            commits_count = 0
            page = 1
            while True:
                params = {
                    "sha": default_branch,
                    "since": since,
                    "until": until,
                    "per_page": 100,
                    "page": page,
                }
                resp = await client.get(commits_url, headers=headers, params=params)
                if resp.status_code in (404, 409):
                    # 404: endpoint ou branch indisponível, 409: branch vazia ou sem HEAD
                    break
                if resp.status_code != 200:
                    raise GitHubReportError(
                        f"Erro ao buscar commits em {repo_path}: {resp.status_code} {resp.text}"
                    )
                data = resp.json()
                if not data:
                    break
                for commit in data:
                    commit_data = commit.get("commit", {})
                    author_info = commit_data.get("author", {})
                    commit_date_str = author_info.get("date")
                    if not commit_date_str:
                        continue
                    commit_dt = datetime.fromisoformat(
                        commit_date_str.replace("Z", "+00:00")
                    )
                    commit_date = commit_dt.date()
                    if not (start_date <= commit_date <= end_date):
                        continue

                    author_name = author_info.get("name") or "Desconhecido"

                    commits_count += 1
                    month_key = commit_date.strftime("%Y-%m")
                    _increment(commits_by_month, month_key)
                    _increment(commits_by_repo, repo_path)
                    _increment(commits_by_author, author_name)

                if len(data) < 100:
                    break
                page += 1

            total_commits += commits_count

            repo_details_lines.append(
                f"**{repo_path}** (branch padrão: {default_branch}): PRs mergeados: {prs_merged_count}, commits: {commits_count}"
            )

    # Destaques
    def _best_entry(d: Dict[str, int]) -> Tuple[Optional[str], int]:
        if not d:
            return None, 0
        key, value = max(d.items(), key=lambda x: x[1])
        return key, value

    best_pr_month, best_pr_month_value = _best_entry(prs_by_month)
    best_commit_month, best_commit_month_value = _best_entry(commits_by_month)
    best_pr_repo, best_pr_repo_value = _best_entry(prs_by_repo)
    best_commit_repo, best_commit_repo_value = _best_entry(commits_by_repo)
    best_pr_author, best_pr_author_value = _best_entry(prs_by_author)
    best_commit_author, best_commit_author_value = _best_entry(commits_by_author)

    start_br = start_date.strftime("%d/%m/%Y")
    end_br = end_date.strftime("%d/%m/%Y")

    header = f"## Relatório GitHub ({start_br} a {end_br})\n\n"

    summary_lines = [
        f"Total de PRs mergeados (todas as partes do sistema): **{total_prs_merged}**",
        f"Total de commits (todas as partes do sistema): **{total_commits}**",
    ]

    highlights_lines = []
    if best_pr_month_value > 0:
        highlights_lines.append(
            f"🏆 Mês com mais PRs: **{best_pr_month}** ({best_pr_month_value} PRs mergeados)"
        )
    if best_commit_month_value > 0:
        highlights_lines.append(
            f"📈 Mês com mais commits: **{best_commit_month}** ({best_commit_month_value} commits)"
        )
    if best_pr_repo_value > 0:
        highlights_lines.append(
            f"📌 Repositório com mais PRs: **{best_pr_repo}** ({best_pr_repo_value} PRs mergeados)"
        )
    if best_commit_repo_value > 0:
        highlights_lines.append(
            f"📌 Repositório com mais commits: **{best_commit_repo}** ({best_commit_repo_value} commits)"
        )
    if best_pr_author_value > 0:
        highlights_lines.append(
            f"⭐ Dev destaque em PRs: **{best_pr_author}** ({best_pr_author_value} PRs mergeados)"
        )
    if best_commit_author_value > 0:
        highlights_lines.append(
            f"⭐ Dev destaque em commits: **{best_commit_author}** ({best_commit_author_value} commits)"
        )

    if longest_pr is not None:
        lt_days = longest_pr["lead_time"].days  # type: ignore[index]
        pr_repo = longest_pr["repo"]  # type: ignore[index]
        pr_number = longest_pr["number"]  # type: ignore[index]
        pr_title = longest_pr["title"]  # type: ignore[index]
        pr_author = longest_pr["author"]  # type: ignore[index]
        highlights_lines.append(
            f"⏱️ Tarefa mais longa (PR): **#{pr_number} - {pr_title}** em `{pr_repo}` por {pr_author} (lead time: {lt_days} dias)"
        )

    # Distribuição mensal
    months = sorted(set(list(prs_by_month.keys()) + list(commits_by_month.keys())))
    monthly_lines = []
    for month in months:
        pr_count = prs_by_month.get(month, 0)
        commit_count = commits_by_month.get(month, 0)
        monthly_lines.append(f"{month}: {pr_count} PRs, {commit_count} commits")

    summary = "\n".join(summary_lines) + "\n\n"

    highlights = ""
    if highlights_lines:
        highlights = "### Destaques do período\n" + "\n".join(highlights_lines) + "\n\n"

    monthly_block = ""
    if monthly_lines:
        monthly_block = "### Entregas por mês\n" + "\n".join(monthly_lines) + "\n\n"

    repos_block = ""
    if repo_details_lines:
        repos_block = "### Por parte do sistema (repositórios)\n" + "\n".join(repo_details_lines) + "\n\n"

    misc_block = ""
    if misc_messages:
        misc_block = "### Observações\n" + "\n".join(misc_messages) + "\n\n"

    return header + summary + highlights + monthly_block + repos_block + misc_block
