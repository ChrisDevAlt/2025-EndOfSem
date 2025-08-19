from pydantic import BaseModel

class AddPatient(BaseModel):
    id: str
    name: str
    phone: str
    condition: str
    notes: str | None
    gender: int
    age: int

