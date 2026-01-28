import uuid
from typing import List
from sqlmodel import Session, select
from fuse.base import CRUDBase
from fuse.datatables.models import DataTable, DataTableRow
from fuse.datatables.schemas import DataTableCreate, DataTableUpdate, DataTableRowCreate, DataTableRowUpdate

class CRUDDataTable(CRUDBase[DataTable, DataTableCreate, DataTableUpdate]):
    def get_by_owner(self, session: Session, owner_id: uuid.UUID) -> List[DataTable]:
        statement = select(self.model).where(self.model.owner_id == owner_id)
        return list(session.exec(statement).all())

class CRUDDataTableRow(CRUDBase[DataTableRow, DataTableRowCreate, DataTableRowUpdate]):
    def get_by_table_id(self, session: Session, table_id: uuid.UUID) -> List[DataTableRow]:
        statement = select(self.model).where(self.model.table_id == table_id)
        return list(session.exec(statement).all())

data_table = CRUDDataTable(DataTable)
data_table_row = CRUDDataTableRow(DataTableRow)
