from fastapi import FastAPI,status
from job_fastapi.config.database import Base,get_db,engine
app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.get("/")
def index():
    return {"status":status.HTTP_200_OK,"message":"Server is running 💀....."}































