import os

import emoji
from azure.devops.v7_1.work_item_tracking import Wiql, WorkItemTrackingClient
from dotenv import load_dotenv

from utils.mercado_topografico.azure_devops.base import AzureMercadoTopografico

load_dotenv()


def estimated_efforts():
    personal_access_token = os.getenv("PERSONAL_ACCESS_TOKEN")
    organization_url = os.getenv("ORGANIZATION_URL")
    project_name = os.getenv("PROJECT_NAME")
    team_name = os.getenv("TEAM_NAME")

    mercado_topografico = AzureMercadoTopografico(
        personal_access_token, organization_url, project_name, team_name
    )

    work_item_query = Wiql(
        query=f"SELECT [System.Id], [System.Title], [System.State] "
        f"FROM WorkItems "
        f"WHERE [System.WorkItemType] IN ('Product Backlog Item', 'Bug') "
        f"AND [System.IterationPath] = '{mercado_topografico.current_sprint_path}'"  # noqa
    )

    work_item_tracking_client = WorkItemTrackingClient(
        organization_url, mercado_topografico.credentials
    )
    work_item_list = work_item_tracking_client.query_by_wiql(work_item_query)

    friendly_message = ("Essas são as **Estimativas para a Sprint"
                        f" {mercado_topografico.current_sprint_number}**:\n\n")

    if work_item_list.work_items is not None:
        for item in work_item_list.work_items:
            work_item = work_item_tracking_client.get_work_item(id=item.id)

            friendly_message += (
                f":small_blue_diamond: {work_item.fields['System.Title']}: "
                f"**{int(work_item.fields.get('Microsoft.VSTS.Scheduling.Effort', 0))}**\n" # noqa
            )

    print(emoji.emojize(":thumbs_up: Estimativas obtidas com sucesso!"))
    return friendly_message


if __name__ == "__main__":
    estimated_efforts()
