import os
from fastapi import FastAPI
import uvicorn
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from aredis import StrictRedis

import logging

urlupdate = FastAPI()
logging.basicConfig(filename='urlupdate.log', level=logging.ERROR)

redis_ip     = os.getenv('DATABASE') if os.getenv('DATABASE') else "redis"
redis_port   = os.getenv('REDIS_PORT') if os.getenv('REDIS_PORT') else "6379"
service_port = os.getenv('PORT') if os.getenv('PORT') else "8091"
ip_addr      = os.getenv('IP') if os.getenv('IP') else "0.0.0.0"

@urlupdate.on_event("startup")
async def startup():
    logging.debug("Starting the URL Update Service")
    urlupdate.client = StrictRedis(host=redis_ip, port=redis_port, db=0)

@urlupdate.on_event("shutdown")
async def shutdown():
    logging.debug("Closing the application")


@urlupdate.get("/help")
def helper():
    return {"urlupdate": "/urlupdate/1/{type}/{hostname_and_port}/{original_path_and_query_string}"}


@urlupdate.exception_handler(StarletteHTTPException)
async def httpExceptionHanlder(Request, exc):
    logging.error("Exception - Invalid  request")
    return JSONResponse(
        status_code=400,
        content={"Cause": "INVALID_URL_ADD_REQUESTED"},
    )

@urlupdate.post("/urlupdate/1/{type}/{hostname_and_port}/{original_path_and_query_string}")
async def urlUpdateSingleEntry(type, hostname_and_port, original_path_and_query_string):
    if not hostname_and_port or not original_path_and_query_string:
        return {"Cause" : "Bad_Request"}
    if type == "single":
        key = hostname_and_port + "/" + original_path_and_query_string
        try:
            found = await urlupdate.client.exists(key)
        except Exception as e:
            logging.error(f"Exception : {e}")
            return JSONResponse(
                status_code=400,
                content={"Cause": "DB_UNAVAILABLE"},
            )
        if found:
            return {"Add" : "Key Exists"}
        else:
            await urlupdate.client.set(key, 1)
            logging.info(f"Key added {key}")
            return {"Add": "URL_ADD_SUCCESS"}
    else:
        return JSONResponse(
             status_code=400,
             content={"Cause": "Use Bulk API"},
        )


@urlupdate.post("/urlupdate/1/bulk/{file_path}")
async def urlUpdateBulkEntry(file_path):
    if not file_path:
        return {"Cause" : "Bad_Request"}
    count = 0
    try:
        block_list_file = open(file_path, 'r')
    except FileNotFoundError:
        return JSONResponse(
            status_code=400,
            content={"Cause": "File Not Found"},
        )
    except:
        return JSONResponse(
            status_code=400,
            content={"Cause": "Unexpected Error"},
        )
    else:
        for line in block_list_file:
            key = line.rstrip('\n')
            try:
                found = await urlupdate.client.exists(key)
            except Exception as e:
                logging.error(f"Exception : {e}")
                return JSONResponse(
                    status_code=400,
                    content={"Cause": "DB_UNAVAILABLE"},
                )  
            if found:
                logging.info(f"existing item: {key}")
            else:
                await urlupdate.client.set(key, 1)
                logging.info(f"new: {key}")
                count += 1

        return {"Add": "BULK_ADD_SUCCESS"}

if __name__ == "__main__":
    logging.info(ip_addr, service_port)
    try:
        uvicorn.run(urlupdate, host=ip_addr, port=service_port)
    except Exception as e:
        logging.error(f"Exception : {e}")



