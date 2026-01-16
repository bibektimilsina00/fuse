from .crud_item import CRUDItem

# Create a crud object similar to the original structure
class CRUD:
    def __init__(self):
        from .models import Item
        self.item = CRUDItem(Item)

crud = CRUD()
