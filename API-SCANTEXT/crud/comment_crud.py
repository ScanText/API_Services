from sqlalchemy.orm import Session
from models.comment_models import Comment
from schemas.comment_schemas import CommentCreate

def create_comment(db: Session, comment: CommentCreate):
    db_comment = Comment(**comment.dict())
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_all_comments(db: Session):
    return db.query(Comment).all()

def get_comments_by_category(db: Session, category: str):
    return db.query(Comment).filter(Comment.category == category).all()
