import datetime

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import IntegrityError
from typing import List

# Создание объекта FastAPI
app = FastAPI()

# Настройка базы данных MySQL
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://isp_p_Kuznetsov:12345@77.91.86.135/isp_p_Kuznetsov"
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


class ProductCreate(BaseModel):
    name: str
    calories_per_100g: float
    weight: int
    price_per_kg: float


class ProductResponse(BaseModel):
    product_id: int
    name: str
    calories_per_100g: float
    weight: int
    price_per_kg: float


class DishCreate(BaseModel):
    name: str
    type: str
    portion_size: int
    image_url: str
    recipes: int
    preparations: int
    ingredients: int


class DishResponse(BaseModel):
    dish_id: int
    name: str
    type: str
    portion_size: int
    image_url: str
    recipes_count: int
    preparations_count: int
    ingredients_count: int


class RecipeCreate(BaseModel):
    dish_id: int
    preparation_time_minutes: int
    cooking_technique: str


class RecipeResponse(BaseModel):
    recipe_id: int
    dish_id: int
    preparation_time_minutes: int
    cooking_technique: str


class PreparationCreate(BaseModel):
    dish_id: int
    portion_count: int
    date: datetime.datetime


class PreparationResponse(BaseModel):
    preparation_id: int
    dish_id: int
    portion_count: int
    date: datetime.datetime


class DishIngredientCreate(BaseModel):
    dish_id: int
    product_id: int
    quantity: int


class DishIngredientResponse(BaseModel):
    dish_id: int
    product_id: int
    quantity: int


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


@app.get("/products/{product_id}", response_model=ProductResponse)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/products/", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    try:
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Product already exists")


@app.get("/dishes/{dish_id}", response_model=DishResponse)
def read_dish(dish_id: int, db: Session = Depends(get_db)):
    dish = db.query(Dish).filter(Dish.dish_id == dish_id).first()
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    return dish


@app.post("/dishes/", response_model=DishResponse)
def create_dish(dish: DishCreate, db: Session = Depends(get_db)):
    db_dish = Dish(
        name=dish.name,
        type=dish.type,
        portion_size=dish.portion_size,
        image_url=dish.image_url,
        recipes_count=dish.recipes,
        preparations_count=dish.preparations,
        ingredients_count=dish.ingredients
    )
    try:
        db.add(db_dish)
        db.commit()
        db.refresh(db_dish)
        return db_dish
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Dish already exists")


@app.get("/recipes/{recipe_id}", response_model=RecipeResponse)
def read_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@app.post("/recipes/", response_model=RecipeResponse)
def create_recipe(recipe: RecipeCreate, db: Session = Depends(get_db)):
    db_recipe = Recipe(
        dish_id=recipe.dish_id,
        preparation_time_minutes=recipe.preparation_time_minutes,
        cooking_technique=recipe.cooking_technique
    )
    try:
        db.add(db_recipe)
        db.commit()
        db.refresh(db_recipe)
        return db_recipe
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Recipe already exists")


@app.get("/preparations/{preparation_id}", response_model=PreparationResponse)
def read_preparation(preparation_id: int, db: Session = Depends(get_db)):
    preparation = db.query(Preparation).filter(Preparation.preparation_id == preparation_id).first()
    if preparation is None:
        raise HTTPException(status_code=404, detail="Preparation not found")
    return preparation


@app.post("/preparations/", response_model=PreparationResponse)
def create_preparation(preparation: PreparationCreate, db: Session = Depends(get_db)):
    db_preparation = Preparation(
        dish_id=preparation.dish_id,
        portion_count=preparation.portion_count,
        date=preparation.date
    )
    try:
        db.add(db_preparation)
        db.commit()
        db.refresh(db_preparation)
        return db_preparation
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Preparation already exists")


@app.get("/dish_ingredients/{dish_ingredient_id}", response_model=DishIngredientResponse)
def read_dish_ingredient(dish_ingredient_id: int, db: Session = Depends(get_db)):
    dish_ingredient = db.query(DishIngredient).filter(DishIngredient.dish_id == dish_ingredient_id).first()
    if dish_ingredient is None:
        raise HTTPException(status_code=404, detail="Dish Ingredient not found")
    return dish_ingredient


@app.post("/dish_ingredients/", response_model=DishIngredientResponse)
def create_dish_ingredient(dish_ingredient: DishIngredientCreate, db: Session = Depends(get_db)):
    db_dish_ingredient = DishIngredient(
        dish_id=dish_ingredient.dish_id,
        product_id=dish_ingredient.product_id,
        quantity=dish_ingredient.quantity
    )
    try:
        db.add(db_dish_ingredient)
        db.commit()
        db.refresh(db_dish_ingredient)
        return db_dish_ingredient
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Dish Ingredient already exists")
