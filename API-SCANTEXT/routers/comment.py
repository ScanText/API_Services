from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from db.database import SessionLocal
from schemas.comment_schemas import CommentCreate, CommentOut
from crud import comment_crud
from models.comment_models import Comment

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=CommentOut)
def create(comment: CommentCreate, db: Session = Depends(get_db)):
    return comment_crud.create_comment(db, comment)

@router.get("/", response_model=List[CommentOut])
def get_all(db: Session = Depends(get_db)):
    return comment_crud.get_all_comments(db)

@router.get("/category/{category}", response_model=List[CommentOut])
def get_by_category(category: str, db: Session = Depends(get_db)):
    return comment_crud.get_comments_by_category(db, category)

@router.get("/stats")
def get_comment_stats(db: Session = Depends(get_db)):
    from models.comment_models import Comment
    from sqlalchemy import func

    stats = (
        db.query(Comment.category, func.count(Comment.id))
        .group_by(Comment.category)
        .all()
    )

    return {category: count for category, count in stats}


@router.get("/by-user/{user_id}", response_model=List[CommentOut])
def get_user_comments(user_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.user_id == user_id).all()
    return comments

@router.delete("/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Комментарий не найден")
    
    db.delete(comment)
    db.commit()
    return {"message": "Комментарий удален"}
