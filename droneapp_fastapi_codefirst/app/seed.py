from app.db import engine, SessionLocal
from app.models.models import SubscriptionPlan, User, InputImage, ProcessingRun, OutputArtifact


def seed():
    with SessionLocal() as session:
        # Create plans
        free = session.query(SubscriptionPlan).filter_by(name='Free').one_or_none()
        if not free:
            free = SubscriptionPlan(name='Free', free_attempts_limit=2)
            session.add(free)
            session.flush()

        pro = session.query(SubscriptionPlan).filter_by(name='Pro').one_or_none()
        if not pro:
            pro = SubscriptionPlan(name='Pro', free_attempts_limit=999999)
            session.add(pro)
            session.flush()

        admin = session.query(User).filter_by(email='admin@droneapp.local').one_or_none()
        if not admin:
            admin = User(
                email='admin@droneapp.local',
                password_hash='fakehash',
                name='Admin',
                role='ADMIN',
                plan_id=free.id,
                free_attempts_used=0,
            )
            session.add(admin)
            session.flush()

        user = session.query(User).filter_by(email='user@droneapp.local').one_or_none()
        if not user:
            user = User(
                email='user@droneapp.local',
                password_hash='fakehash',
                name='User',
                role='USER',
                plan_id=free.id,
                free_attempts_used=1,
            )
            session.add(user)
            session.flush()

        img = InputImage(user_id=user.id, filename='sample.jpg', storage_path='/tmp/sample.jpg')
        session.add(img)
        session.flush()

        run = ProcessingRun(user_id=user.id, input_image_id=img.id, index_type='NDVI', status='SUCCESS')
        session.add(run)
        session.flush()

        out = OutputArtifact(processing_run_id=run.id, artifact_type='VISUAL_PNG', storage_path='/tmp/out.png')
        session.add(out)

        session.commit()


if __name__ == '__main__':
    seed()
