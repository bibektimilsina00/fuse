import uuid
from typing import List
from sqlmodel import Session, select
from fuse.base import CRUDBase
from fuse.datatables.models import DataTable, DataTableRow
from fuse.datatables.schemas import DataTableCreate, DataTableUpdate, DataTableRowCreate, DataTableRowUpdate

from fuse.events.service import event_service

class CRUDDataTable(CRUDBase[DataTable, DataTableCreate, DataTableUpdate]):
    def get_by_owner(self, session: Session, owner_id: uuid.UUID) -> List[DataTable]:
        statement = select(self.model).where(self.model.owner_id == owner_id)
        return list(session.exec(statement).all())

class CRUDDataTableRow(CRUDBase[DataTableRow, DataTableRowCreate, DataTableRowUpdate]):
    def get_by_table_id(self, session: Session, table_id: uuid.UUID) -> List[DataTableRow]:
        statement = select(self.model).where(self.model.table_id == table_id)
        return list(session.exec(statement).all())

    def create_with_event(self, session: Session, *, obj_in: DataTableRowCreate, table_id: uuid.UUID) -> DataTableRow:
        db_obj = self.model(**obj_in.model_dump(), table_id=table_id)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        
        # Dispatch event
        event_service.dispatch("datatables.row_created", {
            "table_id": str(table_id),
            "row_id": str(db_obj.id),
            "data": db_obj.data,
            "action": "created"
        })
        return db_obj

    def update_with_event(self, session: Session, *, db_obj: DataTableRow, obj_in: DataTableRowUpdate) -> DataTableRow:
        updated_obj = super().update(session=session, db_obj=db_obj, obj_in=obj_in)
        
        # Dispatch event
        event_service.dispatch("datatables.row_updated", {
            "table_id": str(updated_obj.table_id),
            "row_id": str(updated_obj.id),
            "data": updated_obj.data,
            "action": "updated"
        })
        return updated_obj

    def remove_with_event(self, session: Session, *, id: uuid.UUID) -> DataTableRow:
        db_obj = session.get(self.model, id)
        if db_obj:
            table_id = db_obj.table_id
            data = db_obj.data
            removed_obj = super().remove(session=session, id=id)
            
            # Dispatch event
            event_service.dispatch("datatables.row_deleted", {
                "table_id": str(table_id),
                "row_id": str(id),
                "data": data,
                "action": "deleted"
            })
            return removed_obj
        return None

data_table = CRUDDataTable(DataTable)
data_table_row = CRUDDataTableRow(DataTableRow)
