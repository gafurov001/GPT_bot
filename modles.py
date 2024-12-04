from sqlalchemy import create_engine, Integer, Text, Select, BigInteger, Delete, String
from sqlalchemy.dialects.postgresql import Insert
from sqlalchemy.orm import DeclarativeBase, declared_attr, Session
from sqlalchemy.orm import Mapped, mapped_column

from config import db_user, db_host, db_name, db_pass, db_port

engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}", echo=True)


class AbstractClass:
    @classmethod
    async def select(cls, **kwargs):
        with engine.connect() as conn:
            res = conn.execute(Select(cls))
            conn.commit()
            return res

    @classmethod
    async def filter(cls, *criteria):
        with engine.connect() as conn:
            res = conn.execute(Select(cls).filter(*criteria))
            conn.commit()
            return res

    @classmethod
    async def create(cls, **kwargs):
        with engine.connect() as conn:
            conn.execute(Insert(cls).values(**kwargs))
            conn.commit()

    @classmethod
    async def delete(cls, id):
        with engine.connect() as conn:
            conn.execute(Delete(cls).where(cls.id==id))
            conn.commit()

    @classmethod
    async def get_or_create(cls, **kwargs):
        with Session(engine) as session:
            get = session.query(cls).filter(**kwargs).first()
            if get:
                return get
            else:
                create = cls(**kwargs)
                session.add(create)
                return create



class Base(DeclarativeBase, AbstractClass):
    @declared_attr
    def __tablename__(self):
        result = self.__name__[0].lower()
        for i in self.__name__[1:]:
            if i.isupper():
                result += f'_{i.lower()}'
                continue
            result += i
        return result


class User(Base):
    id: Mapped[str] = mapped_column(Integer, primary_key=True)
    phone_number: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)


def create_table():
    Base.metadata.create_all(engine)