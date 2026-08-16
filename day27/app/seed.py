from sqlmodel import Session, select

from app.models import Conversation, Experiment, User


SEED_USER_EMAIL = "demo@example.com"


def seed_initial_data(session: Session) -> None:
    """写入一组可用于 Swagger 和前端演示的基础数据。"""
    user = session.exec(
        select(User).where(User.email == SEED_USER_EMAIL)
    ).first()

    if user is None:
        user = User(email=SEED_USER_EMAIL)
        session.add(user)
        session.commit()
        session.refresh(user)

    if user.id is None:
        return

    conversation = session.exec(
        select(Conversation).where(
            Conversation.user_id == user.id,
            Conversation.title == "Docker Compose Demo",
        )
    ).first()

    if conversation is None:
        session.add(
            Conversation(
                user_id=user.id,
                title="Docker Compose Demo",
            )
        )

    seed_experiments = [
        {
            "name": "baseline-f1",
            "model_name": "deepseek-chat",
            "dataset_name": "demo-eval-set",
            "accuracy": 0.82,
            "f1": 0.78,
            "latency_ms": 910.0,
            "cost": 1.25,
            "status": "completed",
        },
        {
            "name": "prompt-v2-f1",
            "model_name": "deepseek-chat",
            "dataset_name": "demo-eval-set",
            "accuracy": 0.86,
            "f1": 0.83,
            "latency_ms": 980.0,
            "cost": 1.42,
            "status": "completed",
        },
        {
            "name": "rag-hybrid-search",
            "model_name": "deepseek-chat",
            "dataset_name": "demo-rag-set",
            "accuracy": 0.88,
            "f1": 0.85,
            "latency_ms": 1240.0,
            "cost": 1.88,
            "status": "completed",
        },
    ]

    for experiment_data in seed_experiments:
        experiment = session.exec(
            select(Experiment).where(
                Experiment.user_id == user.id,
                Experiment.name == experiment_data["name"],
            )
        ).first()

        if experiment is None:
            session.add(
                Experiment(
                    user_id=user.id,
                    **experiment_data,
                )
            )

    session.commit()
