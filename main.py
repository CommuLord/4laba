from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

# Создание объекта FastAPI
app = FastAPI()

# Настройка базы данных MySQL
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://isp_is_test:12345@192.168.25.23/isp_is_test"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Определение модели SQLAlchemy для пользователя
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    email = Column(String(100), unique=True, index=True)

class Dish(Base):
    __tablename__ = "dishes"

    dish_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    type = Column(String(50))
    portion_size = Column(Integer)
    image_url = Column(String(255))
    recipes_count = Column(Integer, default=0)
    preparations_count = Column(Integer, default=0)
    ingredients_count = Column(Integer, default=0)

class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    calories_per_100g = Column(Float)
    weight = Column(Integer)
    price_per_kg = Column(Float)

class Recipe(Base):
    __tablename__ = "recipes"

    recipe_id = Column(Integer, primary_key=True, index=True)
    dish_id = Column(Integer, ForeignKey('dishes.dish_id'))
    preparation_time_minutes = Column(Integer)
    cooking_technique = Column(String(255))

    dish = relationship("Dish", back_populates="recipes")

Dish.recipes = relationship("Recipe", order_by=Recipe.recipe_id, back_populates="dish")

class Preparation(Base):
    __tablename__ = "preparations"

    preparation_id = Column(Integer, primary_key=True, index=True)
    dish_id = Column(Integer, ForeignKey('dishes.dish_id'))
    portion_count = Column(Integer)
    date = Column(DateTime)

    dish = relationship("Dish", back_populates="preparations")

Dish.preparations = relationship("Preparation", order_by=Preparation.preparation_id, back_populates="dish")

class DishIngredient(Base):
    __tablename__ = "dish_ingredients"

    dish_id = Column(Integer, ForeignKey('dishes.dish_id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), primary_key=True)
    quantity = Column(Integer)

    dish = relationship("Dish", back_populates="ingredients")
    product = relationship("Product", back_populates="in_dishes")

Dish.ingredients = relationship("DishIngredient", back_populates="dish")
Product.in_dishes = relationship("DishIngredient", back_populates="product")


# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

# Определение Pydantic модели для пользователя
class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Маршрут для получения пользователя по ID
@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Маршрут для создания нового пользователя
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")