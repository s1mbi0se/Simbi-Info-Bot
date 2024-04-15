import re
import emoji

from azure.devops.connection import Connection
from azure.devops.v7_1.work import TeamContext
from msrest.authentication import BasicAuthentication


class AzureMercadoTopografico:
    def __init__(self, personal_access_token, organization_url, project_name, team_name):
        self.credentials = BasicAuthentication("", personal_access_token)
        self.connection = Connection(base_url=organization_url, creds=self.credentials)
        self.core_client = self.connection.clients.get_core_client()

        self.project_id = self._get_project_id_by_name(self.core_client, project_name)
        self.team_id = self._get_team_id_by_name(self.core_client, team_name, self.project_id)
        self.current_sprint_path, self.current_sprint_number = self._get_current_sprint(self.connection, self.project_id, self.team_id)

    @staticmethod
    def _get_project_id_by_name(core_client, project_name):
        project_id = None
        get_projects_response = core_client.get_projects()
        for project in get_projects_response:
            if project.name == project_name:
                project_id = project.id
                print(emoji.emojize("  :check_mark_button: Nome do projeto"))
        return project_id

    @staticmethod
    def _get_team_id_by_name(core_client, team_name, project_id):
        team_id = None
        get_teams_response = core_client.get_teams(project_id=project_id)
        for team in get_teams_response:
            if team.name == team_name:
                team_id = team.id
                print(emoji.emojize("  :check_mark_button: Informações da equipe"))
        return team_id

    @staticmethod
    def _get_current_sprint(connection, project_id, team_id):
        work_client = connection.clients.get_work_client()
        team_context = TeamContext(project_id=project_id, team_id=team_id)
        current_sprint = work_client.get_team_iterations(
            team_context=team_context, timeframe="Current"
        )
        current_sprint_path = current_sprint[0].path
        current_sprint_path = current_sprint_path.replace("\\", "\\\\")
        current_sprint_number = re.findall(r"\d+", current_sprint[0].name)[0]
        print(emoji.emojize("  :check_mark_button: Dados da sprint atual"))
        return current_sprint_path, current_sprint_number
