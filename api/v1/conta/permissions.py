class UsuarioPermissions:
    SCOPE = "usuario"
    RESOURCE = "linha-cuidado"

    CREATE = f"create:{SCOPE}"
    READ = f"read:{SCOPE}"
    UPDATE = f"update:{SCOPE}"
    DELETE = f"delete:{SCOPE}"
    LIST = f"list:{SCOPE}"
    RESTORE = f"restore:{SCOPE}"
    HARD_DELETE = f"hard_delete:{SCOPE}"
    LIST_DELETED = f"list_deleted:{SCOPE}"

    @classmethod
    def get_all_actions(cls) -> list[str]:
        return [
            cls.CREATE,
            cls.READ,
            cls.UPDATE,
            cls.DELETE,
            cls.LIST,
            cls.RESTORE,
            cls.HARD_DELETE,
            cls.LIST_DELETED,
        ]