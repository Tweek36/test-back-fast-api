from sqlalchemy import Column, BigInteger, String, DateTime, Integer, func, JSON, Boolean, SmallInteger, ARRAY
from schemas import Base


class User(Base):
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, nullable=True)
    username = Column(String, nullable=False)
    email = Column(String, nullable=True)

class UserSecurity(Base):
    __tablename__ = "user_security"

    id = Column(BigInteger, primary_key=True, nullable=True)
    user_id = Column(BigInteger, nullable=False)
    password = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    bad_tokens = Column(DateTime, nullable=True)

class Log(Base):
    __tablename__ = "log"

    id = Column(BigInteger, primary_key=True, nullable=True)
    name = Column(String, nullable=False)
    message = Column(String, nullable=False)
    level = Column(String, nullable=False)
    status_code = Column(Integer, nullable=True)
    url = Column(String, nullable=True)
    time = Column(DateTime, nullable=False, server_default=func.now())
    method = Column(String, nullable=True)
    params = Column(JSON, nullable=True)

class Test(Base):
    __tablename__ = "test"

    id = Column(BigInteger, primary_key=True, nullable=True)
    user_id = Column(BigInteger, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=False)
    image = Column(String, nullable=False)
    published = Column(Boolean, nullable=True, default=False)

class TestItem(Base):
    __tablename__ = "test_item"

    id = Column(BigInteger, primary_key=True, nullable=True)
    test_id = Column(BigInteger, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    videoId = Column(String, nullable=False)

class Tests(Base):
    __tablename__ = "tests"

    id = Column(BigInteger, primary_key=True, nullable=True)
    user_id = Column(BigInteger, nullable=False)
    test_id = Column(BigInteger, nullable=False)
    ended = Column(Boolean, nullable=True, default=False)
    prev_choice = Column(BigInteger, nullable=True)
    cur_choice = Column(BigInteger, nullable=True)
    stage = Column(SmallInteger, nullable=True, default=1)
    items = Column(ARRAY(BigInteger), nullable=True)
    next_items = Column(ARRAY(BigInteger), nullable=True)
    is_refreshed = Column(Boolean, default=False, nullable=True)
    last_update = Column(DateTime, server_default=func.now(), nullable=True)

class Choice(Base):
    __tablename__ = "choice"

    id = Column(BigInteger, primary_key=True, nullable=True)
    tests_id = Column(BigInteger, nullable=False)
    winner_id = Column(BigInteger, nullable=False)
    loser_id = Column(BigInteger, nullable=False)
    stage = Column(SmallInteger, nullable=True, default=1)
