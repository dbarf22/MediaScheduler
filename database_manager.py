import sqlalchemy
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey)

engine = create_engine('sqlite:///ScheduleList.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Schedule(Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    jellyfin_id = Column(String)
    device_id = Column(String)
    title = Column(String)
    scheduled_time = Column(DateTime)
Base.metadata.create_all(engine)

#def getScheduleList():

def addToSchedule(title, jellyfin_id, scheduled_time):
    session = Session()
    # entry = Schedule(title=title, jellyfin_id=jellyfin_id, scheduled_time=scheduled_time)
    # session.add(entry)
    # session.commit()
    session.close()
    print("done")

#def removeFromSchedule():
