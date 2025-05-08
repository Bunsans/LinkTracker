from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from testcontainers.postgres import PostgresContainer

# class MetaSingleton(type):
#     _instances = {}

#     def __call__(cls, *args, **kwargs):
#         if cls not in cls._instances:
#             cls._instances[cls] = super(MetaSingleton, cls).__call__(*args, **kwargs)
#         return cls._instances[cls]


class TestBases:  # (metaclass=MetaSingleton):
    db = None
    main_url = None

    def __init__(self, db_image_name) -> None:
        engine = EngineFactory()
        engine.stand = "localhost"
        # Создание контейнера из образа DB_IMAGE
        postgres_container = PostgresContainer(image=db_image_name)
        self.db = postgres_container.start()
        self.main_url = self.db.get_connection_url()

        BASES = {
            "airline": {"class": Airline_Base, "rows": AIRLINE_ROWS},
            "bookings": {"class": Bookings_Base, "rows": BOOKINGS_ROWS},
        }

        # Создание баз, схем, наполнение данными
        for base_name, base_data in BASES.items():
            self.create_base(base_name=base_name)
            engine.user, engine.passw = "test", "test"
            url = engine.get_postgres_url(base_name=base_name)
            self.create_schema(schema_name=base_name, url=url)
            db_engine = engine.get_engine(base_name)
            base_data.get("class").metadata.create_all(db_engine)

            for __cls, __rows in base_data.get("rows").items():
                db_engine.execute(insert(__cls).values(__rows))

    def create_base(self, base_name) -> None:
        __engine = create_engine(self.main_url)
        __connection = __engine.connect()
        __connection.execution_options(isolation_level="AUTOCOMMIT").execute(
            f"create database {base_name}",
        )
        __host, __port = (
            self.main_url.replace("postgresql+psycopg2://test:test@", "")
            .replace("/test", "")
            .split(":")
        )
        __new_base_url = f"postgresql+psycopg2://test:test@{__host}:{__port}/{base_name}"
        # Добавляем соединение с новой базой в EngineFactory
        __engine = EngineFactory()
        __engine.add_db(base_name=base_name, url=__new_base_url)

    def create_schema(self, url, schema_name) -> None:
        __engine = create_engine(url)
        __connection = __engine.connect()
        __connection.execution_options(isolation_level="AUTOCOMMIT").execute(
            f"create schema {schema_name}",
        )
