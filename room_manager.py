from typing import Optional, List
from sqlalchemy import String, ForeignKey, create_engine, Select
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column, Session, joinedload

# Initializing sqlalchemy engine to handle rooms/patients
engine = create_engine("sqlite+pysqlite:///jobs.sqlite")

class Base(DeclarativeBase):
    pass

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)

    room_id: Mapped[int] = mapped_column(ForeignKey("room_list.room_id"))
    user_id: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)

    description: Mapped[Optional[str]] = mapped_column(String(150))
    likes: Mapped[Optional[str]] = mapped_column(String)

    room: Mapped["Room"] = relationship(back_populates="patients")


class Room(Base):
    __tablename__ = "room_list"

    room_id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str] = mapped_column(String)

    patients: Mapped[List["Patient"]] = relationship(back_populates="room")

#Generates tables into the sqlite file if they are not already there
def generate_tables():
    Base.metadata.create_all(engine)

# Search table for patients by name to get their ids
def search_patients(name):
    with Session(engine) as session:
        query = Select(Patient).options(joinedload(Patient.room)).where(Patient.name.contains(name))
        return session.scalars(query).all()

# Get list of patients associated with a room
def get_patients_in_room(room_number):
    with Session(engine) as session:
        query = Select(Patient).where(Patient.room_id == room_number)
        return session.scalars(query).all()

def add_patient(name, description="N/A", likes="N/A", user_id="N/A", room_id=-1):
    with Session(engine) as session:
        new_patient = Patient(
            room_id=room_id,
            user_id=user_id,
            name=name,
            description=description,
            likes=likes,
        )
        session.add(new_patient)
        session.commit()
