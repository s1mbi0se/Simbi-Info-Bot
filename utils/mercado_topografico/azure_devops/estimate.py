import json
import os

from azure.devops.v7_1.work_item_tracking import Wiql, WorkItemTrackingClient
from dotenv import load_dotenv
from base import AzureMercadoTopografico
load_dotenv()


def get_estimated_efforts():
    personal_access_token = os.getenv("PERSONAL_ACCESS_TOKEN")
    organization_url = os.getenv("ORGANIZATION_URL")
    project_name = os.getenv("PROJECT_NAME")
    team_name = os.getenv("TEAM_NAME")

    mercado_topografico = AzureMercadoTopografico(personal_access_token, organization_url, project_name, team_name)

    work_item_query = Wiql(
        query=f"SELECT [System.Id], [System.Title], [System.State] "
              f"FROM WorkItems "
              f"WHERE [System.WorkItemType] IN ('Product Backlog Item', 'Bug') "
              f"AND [System.IterationPath] = '{mercado_topografico.current_sprint_path}'"
    )

    work_item_tracking_client = WorkItemTrackingClient(
        organization_url, mercado_topografico.credentials
    )
    work_item_list = work_item_tracking_client.query_by_wiql(work_item_query)

    friendly_message = f"Aqui estão as Estimativas para a Sprint {mercado_topografico.current_sprint_number}:\n"

    if work_item_list.work_items is not None:
        for item in work_item_list.work_items:
            work_item = work_item_tracking_client.get_work_item(id=item.id)

            friendly_message += (f"{work_item.fields['System.Title']}: "
                                 f"{int(work_item.fields.get('Microsoft.VSTS.Scheduling.Effort', 0))}\n")

    print(friendly_message)

#     TODO NÃO ESQUECER DO RETURN


if __name__ == "__main__":
    get_estimated_efforts()
