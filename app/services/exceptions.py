class NotFoundError(Exception):
    """Не найдено вхождение в БД"""

    def __init__(self, entity: str, entity_id: str):
        super().__init__(f"{entity} с id={entity_id} не найден(-a)")
