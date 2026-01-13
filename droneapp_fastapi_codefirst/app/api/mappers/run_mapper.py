from app.api.schemas.runs_dto import RunReadDTO


def map_run_to_dto(run) -> RunReadDTO:
    """Automatically map SQLAlchemy ProcessingRun -> RunReadDTO using run.__dict__ and adding user_email."""
    data = dict(run.__dict__)
    # Remove SQLAlchemy instance state if present
    data.pop("_sa_instance_state", None)
    # Add user_email from related user (joinedload expected)
    data["user_email"] = run.user.email if getattr(run, "user", None) else None
    return RunReadDTO(**data)
