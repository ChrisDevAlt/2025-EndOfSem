from sqlmodel import SQLModel, Field, create_engine, Session, select,text
import uuid
import os
from dotenv import load_dotenv
import hashlib
load_dotenv()

class Patient(SQLModel, table=True):
    __tablename__="patients"
    id: str = Field(primary_key=True, index=True)
    name: str
    age: int
    gender: int
    condition: str
    contact: str = Field(index=True)
    note: str | None
    doctor: str = Field(foreign_key="doctors.id")

class Doctor(SQLModel, table=True):
    __tablename__="doctors"
    id: str = Field(default=uuid.uuid4().__str__(), primary_key=True, index=True)
    name: str
    email: str = Field(index=True)
    gender: int
    password: str

class DBApi:
    db_name= os.getenv("DB_NAME")
    db_url = f"sqlite:///{db_name}"

    engine = create_engine(url=db_url, connect_args={"check_same_thread": False})
    def __init__(self, **tables):
        # SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine) ## creating all tables if they don't exist
        
        ## Tables
        self.patient_table = tables["patients"]
        self.doctor_table = tables["doctors"]
        # self.add_doctor(name="John Doe", gender=0, password="secretPassword", email="test@gmail.com")

    def add_doctor(self, name:str, gender:int, password:str, email: str):
        new_doctor= self.doctor_table(name=name, email=email, gender=gender, password=hashlib.sha256(password.encode("utf-8")).hexdigest())
        with Session(self.engine) as session:
            session.add(new_doctor)
            session.commit()
            session.refresh(new_doctor)

    def get_doctor(self, email:str | None, id: str | None):
        try:
            with Session(self.engine) as session:
                statement = select(self.doctor_table).where(self.doctor_table.email==email if email else self.doctor_table.id == id)
                result = session.exec(statement=statement).all()
                return result[0] if len(result) == 1 else []
        except Exception as err:
            print(err)
            return False

    def add_patient(self,doctor: str, name: str, age:int, condition: str, contact: str, note: str | None, gender: int):
        new_patient = self.patient_table(id=uuid.uuid4().__str__(),name=name, age=age, condition=condition, contact=contact, note=note, gender=gender, doctor=doctor)
        with Session(self.engine) as session:
            try:
                session.add(new_patient)
                session.commit()
                session.refresh(new_patient)
            except Exception as err:
                print(err)
                session.rollback()
                return False
        return True
    
    def get_patients(self, doctor: str):
        entries = []
        try:
            with Session(self.engine) as session:
                statement = select(self.patient_table).where(self.patient_table.doctor == doctor)
                result = session.exec(statement=statement)
                patients = result.all()
                for pat in patients:
                    p = {"id": pat.id,"name": pat.name, "age": pat.age, "gender": pat.gender, "condition":pat.condition, "phone":pat.contact}
                    entries.append(p)
        except Exception as err:
            print(err)
            return False
        return entries
    
    
    def delete_patient(self, id: str):
        try:
            with Session(self.engine) as session:
                patient = session.get(self.patient_table, id)
                print(id)
                if not patient:
                    return False
                session.delete(patient)
                session.commit()
        except Exception as err:
            print(err)
            return False
        return True
    

