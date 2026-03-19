# Agents.md - Execution Contract

## Purpose
This document outlines the execution contract that the coding agent must follow.


## Key files
The following files are key to the execution contract:
- `.vibe/plan.md` - A detailed plan for the project.
- `.vibe/brainstorming.md` - A manifest of the project philosophies, ideas, and constraints.
- `.vibe/logs.md` - A log of the agent actions and progress.
- `.vibe/key-decisions.md` - A record of the key decisions made during the project.
- `.vibe/checkpoints.md` - A record of the progress of the project. This is used to pick up the project from where it left off.
- `.vibe/system-design.md` - An outline of the system design of the project.
## Procedure
The agents should follow the following standard procedure:

### Brainstorming Session
At the start of the project, the coding agent work with the user in a brainstorming session to create a detailed plan for the project. The outcome of this session is:
- `.vibe/plan.md` - A detailed plan for the project.
- `.vibe/brainstorming.md` - A manifest of the project philosophies, ideas, and constraints.

### Development Session

The development session is the execution phase that starts after the brainstorming session.
Here is what the process should look like:
1.  The coding agent read the plan and understand the current state of the project.
2.  The coding agent then execute the granular tasks defined in the plan.
3.  After each step is completed, the coding agent logs its progress in the `.vibe/logs.md` file.
4.  If key decisions were made, the coding agent logs them and the rationale for the decision in the `.vibe/key-decisions.md` file. This is used for the future coding agent to stay homogeneous.
5.  If there is a need to modify the plan, goes back to the brainstorming session to modify the plan.
6.  The agents keeps track of the progress in the `.vibe/checkpoints.md` file.
7.  The agents pause and wait for the user to review the progress and provide feedback.

### Review Session
During the review session, the coding agent review the work done so far and make sure it is aligned with the plan.
The agent discusses with the user to improve the work, revert the changes, or modify the plan.


## File Structure

### `.vibe/plan.md`
The plan is a detailed plan for the project.  The plan has 2 levels of granularity:
The top level is a feature / bug fix.
For each feature / bug fix, the agent creates a granular task list.
The format should take into account the following:
- A plan can change, so the plan should have a clear history of changes, a versioning system should be used and it should be easy to revert to a previous version.
- When looking at the plan, it should be clear what is the status of the task (done, in progress, blocked, etc.)
  

### `.vibe/brainstorming.md`
The following file displays the philosophies, ideas, and constraints of the project. It is a sort of context file for the project.
This can be used to guide the future coding agent to stay homogeneous. It can also help planning agents to know the story behind the project.

### `.vibe/logs.md`
The logs are a record of the agent actions and progress. It is used to track the progress of the project and to debug issues.



### `.vibe/key-decisions.md`

### `.vibe/system-design.md`
The system design is an outline of the system design of the project. 
- Functional requirements
- Non-functional requirements
- High-level architecture
- Core Entities
- Data Flow
- API Endpoints
- Database Schema
- Deep Dives


### `.vibe/checkpoints.md`



## Principles


### Coding Principles
- keep the code simple, readable, and modular.
- When developing, stay focused on the task at hand.
- When creating tests, write tests that verify the correctness of the code.
- If tests do not pass, do not modify the test, fix the code.
- A task is complete, until the desired behavior is achieved and the its corresponding tests pass.
- Use `poetry` to manage the dependencies and the project.
- Use `pytest` to run the tests.
- Use `pytest-cov` to generate the coverage report.
- Use `pytest-mock` to mock the dependencies.
- Use `pytest-asyncio` to run the tests asynchronously.
- Use `ruff` to lint the code.
- Use `pyenv` to manage the Python version.
- Use `direnv` to manage the environment variables.
- Only use classes when necessary and prefer functions and modules when possible.
- use `alembic` to manage the database migrations.
- use `sqlalchemy` to interact with the database.
- use `fastapi` to build the API.
- keep `__init__.py` files empty.
- use complete import paths.
- use `release-please` to manage the releases.
- if you are struggling to fix a bug, ask the user for help.
- use type hints effectively.
- write pythonic code.
- in python, use the latest versions of type-hints.
- commits should be atomic and use the conventional commit message format.
- The commit message body can be descriptive of the change, but brief and concise.
- Take the reviewer in consideration when pushing changes. Each commit should be a small change that is easy to review.
- Wait for the review before pushing changes.

### File Structure Principles
Use the following file structure to organize the project:
```
.
├── .vibe/
├── .github/
│   └── workflows/
├── artifacts/
│   ├── datasets/
│   ├── models/
│   └── .gitignore
├── docker/
├── docs/
├── helm/
├── infra/
├── src/
├── notebooks/
├── scripts/
├── tests/
│   ├── integration
│   ├── unit
│   └── __init__.py
├── .dockerignore
├── .env.example
├── .envrc
├── .gitignore
├── .python-version
├── .release-please-manifest.json
├── docker-compose.yml
├── Makefile
├── poetry.lock
├── poetry.toml
├── pyproject.toml
├── README.md
└── release-please-config.json
```
You may need to adapt the file structure to the specific project, but the key files and directories should be the same.


```
# .envrc

VIRTUAL_ENV=".venv"
python_version=$(cat .python-version)
layout pyenv $python_version
layout python
[ -d "$VIRTUAL_ENV" ] && \
    [ ! -e "$VIRTUAL_ENV/bin/poetry" ] && \
    pip install poetry==1.8.2 && \
    pip install keyrings-google-artifactregistry-auth==1.1.2
dotenv_if_exists .env
```