import os

import emoji
from azure.devops.v7_1.work_item_tracking import Wiql, WorkItemTrackingClient
from dotenv import load_dotenv

from utils.mercado_topografico.azure_devops.base import AzureMercadoTopografico

load_dotenv()


def get_azure_work_items():
    personal_access_token = os.getenv("PERSONAL_ACCESS_TOKEN")
    organization_url = os.getenv("ORGANIZATION_URL")
    project_name = os.getenv("PROJECT_NAME")
    team_name = os.getenv("TEAM_NAME")

    mercado_topografico = AzureMercadoTopografico(
        personal_access_token, organization_url, project_name, team_name
    )

    azure_object = get_azure_object(
        organization_url,
        mercado_topografico.credentials,
        project_name,
        mercado_topografico.current_sprint_path,
        mercado_topografico.current_sprint_number,
    )

    return azure_object


def get_azure_object(
    organization_url,
    credentials,
    project_name,
    current_sprint_path,
    current_sprint_number,
):
    effort_dict = {
        "estimated": 0,
        "delivered": 0,
    }
    azure_object = {
        "project": project_name,
        "sprint": current_sprint_number,
        "effort": effort_dict,
        "work_items": [],
        "next_sprint": [],
        "tasks_without_estimates": [],
    }

    print(emoji.emojize(":blue_circle: Obtendo work items da sprint atual"))
    process_work_items_for_sprint(
        organization_url,
        credentials,
        current_sprint_path,
        azure_object,
        is_current_sprint=True,
    )

    print(emoji.emojize(":blue_circle: Obtendo work items da próxima sprint"))
    process_work_items_for_sprint(
        organization_url,
        credentials,
        current_sprint_path,
        azure_object,
    )

    return azure_object


def process_work_items_for_sprint(
    organization_url,
    credentials,
    current_sprint_path,
    azure_object,
    is_current_sprint=False,
):
    effort_estimated_list = []
    effort_delivered_list = []

    state_text = {"In Progress": " (em andamento)", "Waiting": " (aguardando)"}

    if is_current_sprint:
        state_condition = "!= 'New'"
        state_condition_task = "IN ('Done', 'In Progress', 'Waiting')"
        sprint_list = azure_object["work_items"]
    else:
        state_condition = "!= 'Done'"
        state_condition_task = "!= 'Done'"
        sprint_list = azure_object["next_sprint"]

    # Consulta para retornar work items e suas tasks
    work_item_query = Wiql(
        query=f"SELECT [System.Id], [System.Title], [System.State] "
        f"FROM WorkItems "
        f"WHERE [System.WorkItemType] IN ('Product Backlog Item', 'Bug') "
        f"AND [System.State] {state_condition} "
        f"AND [System.IterationPath] = '{current_sprint_path}'"
    )

    work_item_tracking_client = WorkItemTrackingClient(
        organization_url, credentials
    )
    work_item_list = work_item_tracking_client.query_by_wiql(work_item_query)

    if work_item_list.work_items is not None:
        # work_item_list só traz os ids e as urls do work items, nada mais
        for item in work_item_list.work_items:
            # Requisição para trazer mais informações sobre o work item
            work_item = work_item_tracking_client.get_work_item(id=item.id)
            work_item_type = work_item.fields["System.WorkItemType"]
            work_item_type = (
                "PBI"
                if work_item_type == "Product Backlog Item"
                else work_item_type
            )

            work_item_effort = float(
                work_item.fields.get("Microsoft.VSTS.Scheduling.Effort", 0.0)
            )

            effort_estimated_list.append(work_item_effort)

            assigned_to = work_item.fields.get("System.AssignedTo", {})
            assigned_to_name = assigned_to.get(
                "displayName", "Sem responsável"
            )

            work_item_dict = {
                "id": work_item.id,
                "type": work_item_type,
                "state": work_item.fields["System.State"],
                "title": work_item.fields["System.Title"],
                "effort": work_item_effort,
                "assigned_to": assigned_to_name,
                "tasks": [],
            }

            # Consulta para trazer somente Tasks
            task_query = Wiql(
                query=f"SELECT [System.Id],"
                f" [System.Title], [System.WorkItemType] "
                f"FROM WorkItems "
                f"WHERE [System.WorkItemType] IN ('Task', 'Impediment') "
                f"AND [System.State] {state_condition_task} "
                f"AND [System.Parent] = {work_item.id} "
                f"AND [System.IterationPath] = '{current_sprint_path}'"
            )
            task_list = work_item_tracking_client.query_by_wiql(
                wiql=task_query
            )

            if task_list.work_items is not None:
                # task_list só traz os ids e as urls das tasks, nada mais
                for task_item in task_list.work_items:
                    # Requisição para trazer mais informações sobre as tasks
                    task = work_item_tracking_client.get_work_item(
                        id=task_item.id
                    )

                    task_effort = float(
                        task.fields.get(
                            "Microsoft.VSTS.Scheduling.Effort", 0.0
                        )
                    )

                    if task.fields["System.State"] == "Done":
                        effort_delivered_list.append(task_effort)

                    task_title = task.fields["System.Title"]
                    task_state = task.fields["System.State"]

                    if task_state in state_text:
                        task_title += state_text[task_state]

                    if task.fields["System.WorkItemType"] == "Impediment":
                        task_title += " | Impedimento"

                    assigned_to = work_item.fields.get("System.AssignedTo", {})
                    assigned_to_name = assigned_to.get(
                        "displayName", "Sem responsável"
                    )

                    task_dict = {
                        "task_id": task.id,
                        "task_type": task.fields["System.WorkItemType"],
                        "task_state": task_state,
                        "task_title": task_title,
                        "task_effort": task_effort,
                        "task_assigned_to": assigned_to_name,
                    }
                    work_item_dict["tasks"].append(task_dict)

                    if (
                        is_current_sprint
                        and task_effort == 0.0
                        and task_state == "Done"
                    ):
                        azure_object["tasks_without_estimates"].append(
                            task_dict
                        )

            sprint_list.append(work_item_dict)

    if is_current_sprint:
        azure_object["effort"]["estimated"] = sum(effort_estimated_list)
        azure_object["effort"]["delivered"] = sum(effort_delivered_list)


def get_tasks_without_estimates(tasks_without_estimates):
    message = ""
    if len(tasks_without_estimates) > 0:
        message = "## Atenção, há tarefas concluídas sem estimativa: \n"
        for task in tasks_without_estimates:
            message += (
                f":small_orange_diamond: **{task['task_assigned_to']}** - "
                f"{task['task_id']} "
                f"{task['task_title']}\n"
            )
    else:
        message += (
            "**Todas as tarefas concluídas foram estimadas** "
            ":ballot_box_with_check:"
        )

    return message


if __name__ == "__main__":
    get_azure_work_items()
