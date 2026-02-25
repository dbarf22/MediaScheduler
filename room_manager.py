from typing import Optional, List
from sqlalchemy import String, ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column, Session

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
        session.query()


def add_patient(name, description="N/A", likes="N/A", user_id="N/A", room_id=-1):
    with Session(engine) as session:

        room_check = session.get(Room, room_id)
        if not room_check:
            print(f"Error: Room {room_id} is invalid.")

        new_patient = Patient(
            room_id=room_id,
            user_id=user_id,
            name=name,
            description=description,
            likes=likes,
        )
        session.add(new_patient)
        session.commit()
