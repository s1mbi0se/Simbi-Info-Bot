import os
from datetime import date

from azure.devops.v7_1.work_item_tracking import Wiql, WorkItemTrackingClient
from dotenv import load_dotenv

from utils.mercado_topografico.azure_devops.base import AzureMercadoTopografico

load_dotenv()


def get_report_data(start_date: date, end_date: date) -> dict:
    if start_date > end_date:
        raise ValueError("Data inicial maior que data final")

    personal_access_token = os.getenv("PERSONAL_ACCESS_TOKEN")
    organization_url = os.getenv("ORGANIZATION_URL")
    project_name = os.getenv("PROJECT_NAME")
    team_name = os.getenv("TEAM_NAME")

    if not all([personal_access_token, organization_url, project_name, team_name]):
        raise RuntimeError(
            "Variáveis de ambiente do Azure DevOps não configuradas corretamente"
        )

    mt = AzureMercadoTopografico(
        personal_access_token, organization_url, project_name, team_name
    )

    client = WorkItemTrackingClient(organization_url, mt.credentials)

    start_iso = start_date.strftime("%Y-%m-%d")
    end_iso = end_date.strftime("%Y-%m-%d")

    # PBIs e Bugs concluídos no período (para esforço total e contagem de PBIs/Bugs)
    pbi_query = Wiql(
        query=(
            "SELECT [System.Id] "
            "FROM WorkItems "
            "WHERE [System.TeamProject] = '{project}' "
            "AND [System.WorkItemType] IN ('Product Backlog Item', 'Bug') "
            "AND [System.State] = 'Done' "
            "AND [Microsoft.VSTS.Common.ClosedDate] >= '{start}' "
            "AND [Microsoft.VSTS.Common.ClosedDate] <= '{end}'"
        ).format(project=project_name, start=start_iso, end=end_iso)
    )

    pbi_list = client.query_by_wiql(pbi_query)

    pbi_done = 0
    total_effort = 0.0

    if pbi_list.work_items is not None:
        for item in pbi_list.work_items:
            work_item = client.get_work_item(id=item.id)
            effort = float(
                work_item.fields.get("Microsoft.VSTS.Scheduling.Effort", 0.0)
            )
            total_effort += effort
            pbi_done += 1

    # Tasks concluídas no período (todas)
    task_query = Wiql(
        query=(
            "SELECT [System.Id] "
            "FROM WorkItems "
            "WHERE [System.TeamProject] = '{project}' "
            "AND [System.WorkItemType] = 'Task' "
            "AND [System.State] = 'Done' "
            "AND [Microsoft.VSTS.Common.ClosedDate] >= '{start}' "
            "AND [Microsoft.VSTS.Common.ClosedDate] <= '{end}'"
        ).format(project=project_name, start=start_iso, end=end_iso)
    )

    task_list = client.query_by_wiql(task_query)

    task_done = 0

    if task_list.work_items is not None:
        for item in task_list.work_items:
            client.get_work_item(id=item.id)
            task_done += 1

    return {
        "start_date": start_date,
        "end_date": end_date,
        "pbi_done": pbi_done,
        "task_done": task_done,
        "total_effort": total_effort,
    }


def format_report_message(report_data: dict) -> str:
    start_date = report_data["start_date"]
    end_date = report_data["end_date"]
    pbi_done = report_data["pbi_done"]
    task_done = report_data["task_done"]
    total_effort = report_data["total_effort"]

    start_br = start_date.strftime("%d/%m/%Y")
    end_br = end_date.strftime("%d/%m/%Y")

    header = f"## Relatório de entrega ({start_br} a {end_br})\n\n"

    if pbi_done == 0 and task_done == 0:
        body = "Nenhum PBI ou Task concluído nesse período para este projeto."
        return header + body

    body = (
        f":white_check_mark: PBIs/Bugs concluídos: **{pbi_done}**\n"
        f":white_check_mark: Tasks concluídas: **{task_done}**\n"
        f":large_blue_diamond: Pontos entregues (Effort): **{total_effort}**\n\n"
    )

    footer = (
        "Bom trabalho! Esses são os itens concluídos nesse período no Mercado Topográfico."
    )

    return header + body + footer


def generate_period_report(start_date: date, end_date: date) -> str:
    report_data = get_report_data(start_date, end_date)
    return format_report_message(report_data)
