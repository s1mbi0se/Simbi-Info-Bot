import os.path

import emoji
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from utils.mercado_topografico.azure_devops.work_items import (
    get_azure_work_items,
    get_tasks_without_estimates,
)

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
]


def generate_presentation():
    creds = Credentials.from_service_account_file(
        "credentials.json", scopes=SCOPES
    )
    try:
        print(
            emoji.emojize(
                ":green_circle: Autenticado. Começando o processo..."
            )
        )
        slide_template_id = os.getenv("SLIDE_TEMPLATE_ID")
        slide_service = build("slides", "v1", credentials=creds)
        drive_service = build("drive", "v3", credentials=creds)

        print(
            emoji.emojize(":blue_circle: Obtendo informações no Azure Devops")
        )
        azure_object = get_azure_work_items()

        tasks_without_estimates = azure_object["tasks_without_estimates"]
        message_tasks = get_tasks_without_estimates(tasks_without_estimates)
        if not message_tasks["all_estimated"]:
            current_sprint = None
            tasks_without_estimates = None
            presentation_url = None
            return (
                current_sprint,
                tasks_without_estimates,
                presentation_url,
                message_tasks,
            )

        print(
            emoji.emojize(
                ":blue_circle: Criando a apresentação no Google Drive"
            )
        )
        presentation_copy_id = create_copy_of_presentation(
            drive_service, slide_template_id, azure_object
        )
        next_sprint_number = int(azure_object["sprint"]) + 1

        print(emoji.emojize(":blue_circle: Alterando textos globalmente"))
        replacements = [
            ("{{sprint}}", azure_object["sprint"]),
            ("{{next_s}}", str(next_sprint_number)),
            ("{{eff_estimated}}", str(azure_object["effort"]["estimated"])),
            ("{{eff_delivered}}", str(azure_object["effort"]["delivered"])),
        ]
        for search, replace in replacements:
            replace_text_globally(
                slide_service,
                presentation_copy_id,
                search,
                replace,
            )

        presentation_copy = (
            slide_service.presentations()
            .get(presentationId=presentation_copy_id)
            .execute()
        )

        # Posição exata (index) dos slides que serão clonados.
        item_slide_original_index = 2
        item_slide_original_id = presentation_copy.get("slides")[
            item_slide_original_index
        ]["objectId"]

        next_sprint_item_slide_index = 5
        next_sprint_item_slide_id = presentation_copy.get("slides")[
            next_sprint_item_slide_index
        ]["objectId"]

        items_per_slide = 3
        items_per_slide_next_sprint = 6

        print(emoji.emojize(":blue_circle: Gerando slides com work items"))
        generate_slides_with_work_items(
            slide_service,
            presentation_copy_id,
            items_per_slide,
            items_per_slide_next_sprint,
            azure_object,
            item_slide_original_id,
            next_sprint_item_slide_id,
        )

        print(emoji.emojize(":fire: Deletando slides de referência"))
        delete_slide(
            slide_service, presentation_copy_id, item_slide_original_id
        )
        delete_slide(
            slide_service, presentation_copy_id, next_sprint_item_slide_id
        )

        print(emoji.emojize(":fire: Limpando variáveis não usadas"))
        clear_unused_variables_globally(
            slide_service,
            presentation_copy_id,
            max_ids_in_presentation=items_per_slide_next_sprint,
        )

        print(
            emoji.emojize(":thumbs_up: Apresentação foi gerada com sucesso!")
        )

        current_sprint = azure_object["sprint"]
        tasks_without_estimates = azure_object["tasks_without_estimates"]
        presentation_url = (
            f"https://docs.google.com/presentation/d/{presentation_copy_id}"
        )
        return (
            current_sprint,
            tasks_without_estimates,
            presentation_url,
            message_tasks,
        )

    except HttpError as err:
        print(err)


def generate_slides_with_work_items(
    slide_service,
    presentation_copy_id: str,
    items_per_slide: int,
    items_per_slide_next_sprint: int,
    azure_object,
    item_slide_original_id: str,
    next_sprint_item_slide_id: str,
):
    number_of_slides_created = []
    item_slide_copy_id = ""

    # Iteração em work items da sprint atual e da próxima
    for iteration_index, (items_list, initial_slide_id) in enumerate(
        [
            (azure_object["work_items"], item_slide_original_id),
            (azure_object["next_sprint"], next_sprint_item_slide_id),
        ]
    ):
        total_list_items = len(items_list)
        current_sprint = 0
        if iteration_index == current_sprint:
            for index in range(total_list_items):
                # Cria um novo slide a cada 3 work items
                if index % items_per_slide == 0:
                    number_of_slides_created.append(index)
                    item_slide_copy_id = create_copy_of_item_slide_original(
                        slide_service, presentation_copy_id, initial_slide_id
                    )
                # Altera os valores de uma coluna do slide por vez
                replace_text_in_each_column_of_the_item_slide_copy(
                    slide_service,
                    presentation_copy_id,
                    item_slide_copy_id,
                    index,
                    items_list[index],
                )
        else:
            for index in range(total_list_items):
                # Novo slide a cada 6 work items para a próxima sprint
                if index % items_per_slide_next_sprint == 0:
                    number_of_slides_created.append(index)
                    item_slide_copy_id = create_copy_of_item_slide_original(
                        slide_service, presentation_copy_id, initial_slide_id
                    )
                # Altera os valores de uma coluna do slide por vez
                replace_text_in_each_column_next_sprint(
                    slide_service,
                    presentation_copy_id,
                    item_slide_copy_id,
                    index,
                    items_list[index],
                )

    print(
        emoji.emojize(
            f"  :check_mark_button: {len(number_of_slides_created)} "
            f"slides criados com sucesso."
        )
    )


def create_copy_of_presentation(
    drive_service, slide_template_id: str, azure_object
):
    project_name = os.getenv("PROJECT_NAME")
    body = {"name": f"{project_name} - Sprint {azure_object['sprint']}"}
    response = (
        drive_service.files()
        .copy(fileId=slide_template_id, body=body)
        .execute()
    )
    new_presentation_id = response.get("id")
    print(
        emoji.emojize(
            f"  :check_mark_button: "
            f"Apresentação criada com id {new_presentation_id}"
        )
    )
    return new_presentation_id


def create_copy_of_item_slide_original(
    slide_service, presentation_id: str, item_slide_original_id: str
):
    body = {
        "requests": [{"duplicateObject": {"objectId": item_slide_original_id}}]
    }
    response = (
        slide_service.presentations()
        .batchUpdate(presentationId=presentation_id, body=body)
        .execute()
    )
    new_item_slide_id = response["replies"][0]["duplicateObject"]["objectId"]
    print(
        emoji.emojize(
            f"  :check_mark_button: "
            f"Criado uma cópia do slide original com id {new_item_slide_id}"
        )
    )
    return new_item_slide_id


def replace_text_globally(
    slide_service, presentation_id: str, old_text: str, new_text: str
):
    body = {
        "requests": [
            {
                "replaceAllText": {
                    "containsText": {"text": old_text},
                    "replaceText": new_text,
                }
            }
        ]
    }
    slide_service.presentations().batchUpdate(
        presentationId=presentation_id, body=body
    ).execute()
    print(
        emoji.emojize(
            f"  :check_mark_button: "
            f"Texto alterado de '{old_text}' para '{new_text}'"
        )
    )


def replace_text_in_each_column_of_the_item_slide_copy(
    slide_service,
    presentation_id: str,
    slide_id: int,
    index: int,
    azure_work_items,
):
    tasks_text = ""
    for i, task in enumerate(azure_work_items["tasks"]):
        tasks_text += f"{task['task_title']}"
        if i < len(azure_work_items["tasks"]) - 1:
            tasks_text += "\n"

    # Intervado de 1 a 3 sempre
    index_range: str = str(1 + (index % 3))

    body = {
        "requests": [
            {
                "replaceAllText": {
                    "containsText": {"text": "{{type_" + index_range + "}}"},
                    "replaceText": azure_work_items["type"],
                    "pageObjectIds": [slide_id],
                }
            },
            {
                "replaceAllText": {
                    "containsText": {"text": "{{id_" + index_range + "}}"},
                    "replaceText": str(azure_work_items["id"]),
                    "pageObjectIds": [slide_id],
                }
            },
            {
                "replaceAllText": {
                    "containsText": {"text": "{{title_" + index_range + "}}"},
                    "replaceText": azure_work_items["title"],
                    "pageObjectIds": [slide_id],
                }
            },
            {
                "replaceAllText": {
                    "containsText": {"text": "{{task_" + index_range + "}}"},
                    "replaceText": tasks_text,
                    "pageObjectIds": [slide_id],
                }
            },
        ]
    }
    slide_service.presentations().batchUpdate(
        presentationId=presentation_id, body=body
    ).execute()
    print(
        emoji.emojize(
            f"      :check_mark_button:"
            f" Texto adicionado na Coluna {index_range} do Slide id {slide_id}"
        )
    )


def replace_text_in_each_column_next_sprint(
    slide_service,
    presentation_id: str,
    slide_id: int,
    index: int,
    azure_work_items,
):

    # Intervado de 1 a 6 sempre
    index_range: str = str(1 + (index % 6))

    body = {
        "requests": [
            {
                "replaceAllText": {
                    "containsText": {"text": "{{type_" + index_range + "}}"},
                    "replaceText": azure_work_items["type"],
                    "pageObjectIds": [slide_id],
                }
            },
            {
                "replaceAllText": {
                    "containsText": {"text": "{{id_" + index_range + "}}"},
                    "replaceText": str(azure_work_items["id"]),
                    "pageObjectIds": [slide_id],
                }
            },
            {
                "replaceAllText": {
                    "containsText": {"text": "{{title_" + index_range + "}}"},
                    "replaceText": azure_work_items["title"],
                    "pageObjectIds": [slide_id],
                }
            },
        ]
    }
    slide_service.presentations().batchUpdate(
        presentationId=presentation_id, body=body
    ).execute()
    print(
        emoji.emojize(
            f"      :check_mark_button:"
            f" Texto adicionado na Coluna {index_range} do Slide id {slide_id}"
        )
    )


def clear_unused_variables_globally(
    slide_service, presentation_id, max_ids_in_presentation
):
    for index in range(max_ids_in_presentation):
        index_range: str = str(index + 1)
        body = {
            "requests": [
                {
                    "replaceAllText": {
                        "containsText": {
                            "text": "{{type_" + index_range + "}}"
                        },
                        "replaceText": "",
                    }
                },
                {
                    "replaceAllText": {
                        "containsText": {"text": "{{id_" + index_range + "}}"},
                        "replaceText": "",
                    }
                },
                {
                    "replaceAllText": {
                        "containsText": {
                            "text": "{{title_" + index_range + "}}"
                        },
                        "replaceText": "",
                    }
                },
                {
                    "replaceAllText": {
                        "containsText": {
                            "text": "{{task_" + index_range + "}}"
                        },
                        "replaceText": "",
                    }
                },
            ]
        }
        slide_service.presentations().batchUpdate(
            presentationId=presentation_id, body=body
        ).execute()


def delete_slide(slide_service, presentation_id: str, slide_id: str):
    body = {"requests": [{"deleteObject": {"objectId": slide_id}}]}
    slide_service.presentations().batchUpdate(
        presentationId=presentation_id, body=body
    ).execute()
    print(
        emoji.emojize(
            f"  :check_mark_button: Slide deletado com id {slide_id}"
        )
    )


if __name__ == "__main__":
    generate_presentation()
