from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import UserORM

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def get_all(self) -> list[UserORM]:
        return self.db.scalars(select(UserORM)).all()
    
    def get_by_id(self, user_id: str) -> UserORM:
        return self.db.get(UserORM, user_id)
    
    def create(self, email: str, login: str, password: str) -> UserORM:
        new = UserORM(email=email, login=login, password=password)
        self.db.add(new)
        return new
    
    def delete(self, inst: UserORM) -> None:
        self.db.delete(inst)