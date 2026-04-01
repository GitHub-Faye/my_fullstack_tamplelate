from fastapi import Depends, FastAPI,Path, Query ,Body, Cookie, Header, Form, File, UploadFile, HTTPException

from pydantic import BaseModel, Field

from typing import Annotated, Literal
from enum import Enum

app = FastAPI()





# http://127.0.0.1:8000/items/3 接收路径参数
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]
#http://127.0.0.1:8000/items/?skip=0&limit=10 接收查询参数的值
@app.get("/items/")
async def read_item(skip: int = 0, limit: int  | None = 10):
    return fake_items_db[skip : skip + limit]


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@app.post("/items/")
async def create_item(item: Item):
    return item


#annotated type hints with Path() to declare more metadata and validation rules for path parameters
@app.get("/items/{item_id}")
async def read_items(
    item_id: Annotated[int, Path(title="The ID of the item to get")],
):
    results = {"item_id": item_id}
    return results



#annotated type hints with Query() to declare more metadata and validation rules for query parameters
@app.get("/items/")
async def read_items(
    q: Annotated[
        str | None,
        Query(
            alias="item-query",
            title="Query string",
            description="Query string for the items to search in the database that have a good match",
            min_length=3,
            max_length=50,
            pattern="^fixedquery$",
            deprecated=True,
        ),
    ] = None,
):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results

#使用Annotated和Query() 将查询参数声明为一个Pydantic v2 模型，
class FilterParams(BaseModel):
    model_config = {"extra": "forbid"}

    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []
@app.get("/items/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query


#使用Annotated和Body() 将请求体参数声明为一个Pydantic v2 模型，Body()函数的embed参数设置为True，表示将请求体参数嵌套
class Item(BaseModel):
    name: str
    description: str | None = Field(
        default=None, title="The description of the item", max_length=300
    )
    price: float = Field(gt=0, description="The price must be greater than zero")
    tax: float | None = None
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Annotated[Item, Body(embed=True)]):
    results = {"item_id": item_id, "item": item}
    return results




@app.get("/items/")
async def read_items(ads_id: Annotated[str | None, Cookie()] = None):
    return {"ads_id": ads_id}

@app.get("/items/")
async def read_items(user_agent: Annotated[str | None, Header()] = None):
    return {"User-Agent": user_agent}


# 字符串枚举类型 Enum由元类构造，Enum成员是类属性，成员值是字符串
class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"
# 通过枚举类型来限定路径参数的值，只有枚举成员的值才是合法的路径参数值
# 将枚举成员返回，会自动转换为字符串类型的值，返回给客户端。
@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


class FormData(BaseModel):
    username: str
    password: str
@app.post("/login/")
async def login(data: Annotated[FormData, Form()]):
    return data

@app.post("/uploadfile/")
async def create_upload_file(
    file: Annotated[UploadFile, File(description="A file read as UploadFile")],
):
    return {"filename": file.filename}





class Item(BaseModel):
    id: int
    name: str
    description: str | None = None
# 假设从数据库返回的是 dict 或 ORM 对象
fake_db_item = {"id": 1, "name": "Foo", "description": "Bar", "secret": "隐藏字段"}

@app.get("/items/{item_id}", response_model=Item)  # 这里指定
async def read_item(item_id: int):
    # 实际返回 dict 或其他对象也没关系
    return fake_db_item   # FastAPI 会自动过滤，只保留 Item 定义的字段

@app.get("/items/{item_id}")
async def read_item(item_id: int) -> Item:   # 用 ->
    item = Item(id=1, name="Foo", description="Bar")
    return item   # 必须返回 Item 实例，否则编辑器会报类型错误

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(name: str):
    return {"name": name}

@app.get("/items-header/{item_id}")
async def read_item_header(item_id: str):
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "There goes my error"},
        )
    return {"item": items[item_id]}


async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: Annotated[dict, Depends(common_parameters)]):
    return commons