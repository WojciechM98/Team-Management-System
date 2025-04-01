from sqlalchemy import TypeDecorator, VARCHAR
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema
import bcrypt

class PasswordHash():
    def __init__(self, hash):
        assert len(hash) == 60, 'Bcrypt hash sould be 60 characters long.'
        assert str(hash).count('$'), 'Bcrypt has should have 3 "$" signs'
        self.hash = str(hash)
        self.rounds = int(self.hash.split('$')[2])

    def __repr__(self):
        return f'<{type(self).__name__}>'

    @classmethod
    def new(cls, password: str, rounds: int = 12):
        return cls(bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds)).decode())
    
    @staticmethod
    def check(plain_password: str, hashed_password: str):
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

class Password(TypeDecorator):
    impl = VARCHAR

    def __init__(self, rounds=12, **kwargs):
        self.rounds = rounds
        super().__init__(**kwargs)

    def process_bind_param(self, value, dialect):
        """Ensure value to be PasswordHash"""
        return self._convert(value).hash

    def process_result_value(self, value, dialect):
        """Convert the hash to a PasswordHash"""
        if value is not None:
            return PasswordHash(value) 
        else:
            return None
    
    def validator(self, password):
        return self._convert(password)

    def _convert(self, value):
        """Returns a PaswordHash from a given string."""
        if isinstance(value, PasswordHash):
            return value
        elif isinstance(value, str):
            return PasswordHash.new(value, self.rounds)
        elif value is not None:
            raise TypeError(f'Cannot convert {type(value)} to a PasswordHash')



# a = PasswordHash.new('wojtekmajnert', 9)
# print(a.check('wojtekmajnert'))
# print(f'\n\n\n{a.check("msfdjj")}')