from supabase import create_client

from config import Config


class SupabaseClient:
    @staticmethod
    def create_task(task: str, created_by_id: int, created_by_name: int, created_to_id: int, created_to_name: int):
        SUPABASE_CLIENT = create_client(Config().SUPABASE_URL, Config().SUPABASE_KEY)
        table_name = "task"
        task_data = {
            "task": task,
            "created_by_id": created_by_id,
            "created_by_name": created_by_name,
            "created_to_id": created_to_id,
            "created_to_name": created_to_name,
            "active": True
        }
        data, count = SUPABASE_CLIENT.table(table_name).insert(task_data).execute()
        return len(data[1]) > 0


