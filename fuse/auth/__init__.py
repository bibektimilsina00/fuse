from .crud_user import CRUDUser

# Create a crud object similar to the original structure
class CRUD:
    def __init__(self):
        from .models import User
        self.user = CRUDUser(User)

crud = CRUD()
