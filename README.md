
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-A52A2A?style=for-the-badge&link=https%3A%2F%2Fimg.shields.io%2Fbadge%2FSQLachemy-8A2BE2)



# Task Management System

Task Management Software is an application that enables users to manage tasks in a simple and secure way. The application consists of a FastAPI-based backend that allows users to create, edit, and track their tasks. At the moment the frontend does not exist, but it will be created in the future.




## Features

- User registration and login (JWT Authentication)
- Secure password storage (bcrypt)
- Creating, editing, and deleting tasks
- Adding comments to tasks
- Managing task status




## Tech Stack

**Backend:** FastAPI, SQLAlchemy, Postgresql

**Seciurity:** OAuth2, Bcrypt, JWT



## Installation and setup

Clone the repository

```bash
  git clone https://github.com/WojciechM98/Team-Management-System.git
  cd Team-Management-System
```

Install pipenv

```bash
  pip install pipenv
```

Install dependencies using Pipfile cloned with repository

```bash
  pipenv install
```

Next activate pipenv shell

```bash
  pipenv shell
```

### Environment Variables

Now create a .env file that will store the environment variables used during OAuth2 authentication

```bash
  touch .env
```

Add following environment variables:

`DATABASE_USER = <string>` - database username

`DATABASE_PASSWORD = <string>` - database password

`SECRET_KEY = <string>` - a string used to sign JWT tokens. To generate proper `SECRET_KEY` use:
```bash
  openssl rand -hex 32
```

`ALGORITHM = "HS256"` - algorithm used to sign the JWT token

`ACCESS_TOKEN_EXPIRE = <integer>` - constant to set expiration time in minutes

### Create database

You have just prepared the environment and downloaded all the dependencies. All that is left is to create a local database using postgresql. A great postgresql installation guide is [here](https://www.w3schools.com/postgresql/postgresql_install.php)

Now everything is setup and ready to go!
## OAuth2 user authentication
The authentication process uses Bearer **JWT (JSON Web Tokens)**. FastAPI has a built-in **OAuth2** authorization protocol, which was used in this case.
The code below shows the user authorization route using the *OAuth2PasswordRequestForm* form included by FastAPI.
```python
@app.post('/token')
async def login_for_access_token(form_data: Annotated[sc.OAuth2PasswordRequestForm, Depends()],
                                 instance: Session = Depends(db.get_session)) -> sc.Token:
    result = sc.login_for_access_token_function(form_data, instance)
    return result
```
## Password security
In order to store the password securely in the database, the **Bcrypt** hashing algorithm was used.
With custom **PasswordHash** class:
```python
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
```
easily perform the operation of creating a new password and verifying the plain text password with the user's password stored in the database.
## Test run

To run the application, simply run:

```bash
  fastapi dev main.py
```

The following examples show how the application works.

Creating new user

![create_user](https_link)

Logging in to the newly created account

![login](https_link)

Show all users

![show_users](https_link)

Creating a new task

![new_task](https_link)

Assigning user to task

![assign_user_to_task](https_link)

Adding a comment to a task

![new_comment](https_link)

Show all tasks

![show_tasks](https_link)