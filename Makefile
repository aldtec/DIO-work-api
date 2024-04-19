run:
	@uvicorn workout_api.main:app --reload

create-migrations:
	@PYTHONPATH=$PYTHONPATH:$(pwd) alembic revision --autogenerate -m $(d)

run-migrations:
	@PYTHONPATH=$PYTHONPATH:$(pwd) alembic upgrade head

# alembic init alembic
# alembic revision -m "<mensagem>"
# alembic upgrade head
# env\scripts\activate
