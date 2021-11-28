import os
from fastapi import FastAPI
import uvicorn
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from aredis import StrictRedis
#from urlupdate_timer import registerUrlUpdateTimer

import logging

urlapp = FastAPI()
logging.basicConfig(filename='urlapp.log', level=logging.ERROR)

class stats(object):
    def __init__(self):
        self.total_req_count       = 0
        self.malware_detected      = 0
        self.malware_not_detected  = 0
        self.total_failed_req      = 0

    def add_total_req_count(self):
        self.total_req_count +=1

    def add_malware_detected(self):
        self.malware_detected +=1

    def add_malware_not_detected(self):
        self.malware_not_detected +=1

    def add_total_failed_req(self):
        self.total_failed_req += 1

redis_ip     = os.getenv('DATABASE') if os.getenv('DATABASE') else "redis"
redis_port   = os.getenv('REDIS_PORT') if os.getenv('REDIS_PORT') else "6379"
service_port = os.getenv('APP_PORT') if os.getenv('APP_PORT') else "8090"
ip_addr      = os.getenv('IP') if os.getenv('IP') else "0.0.0.0"

req_stats = stats()

@urlapp.on_event("startup")
async def startup():
    logging.debug("Starting the URL Lookup Service")
    urlapp.client = StrictRedis(host=redis_ip, port=redis_port, db=0)

@urlapp.on_event("shutdown")
async def shutdown():
    logging.debug("Closing the application")
    #registerUrlUpdateTimer("0")


@urlapp.get("/urlinfo/help")
def helper():
    return {"urllookup": "/urlinfo/1/{hostname_and_port}/{original_path_and_query_string}"}

@urlapp.get("/urlinfo/stats")
def urlappStats():
    logging.debug("Get Statistics")
    logging.info(f"Total reqs :{req_stats.total_req_count} Total Failed req: {req_stats.total_failed_req}"
                 f"Total Malware detected: {req_stats.malware_detected}, Total Good Req : {req_stats.malware_not_detected}")

    return {"Service Name":" ",
            "Total Requests": str(req_stats.total_req_count + req_stats.total_failed_req),
            "Malwares_detected" : str(req_stats.malware_detected),
            "Malwares_not_detected" : str(req_stats.malware_not_detected)}

@urlapp.exception_handler(StarletteHTTPException)
async def httpExceptionHanlder(Request, exc):
    req_stats.add_total_failed_req()
    logging.error("Exception - Invalid URL request")
    return JSONResponse(
        status_code=400,
        content={"Cause": "INVALID_URL_REQUESTED"},
    )

@urlapp.post("/urlupdate/1/{type}/{hostname_and_port}/{original_path_and_query_string}")
async def urlUpdateSingleEntry(type, hostname_and_port, original_path_and_query_string):
    if not hostname_and_port or not original_path_and_query_string:
        return {"Cause" : "Bad_Request"}
    if type == "single":
        key = hostname_and_port + "/" + original_path_and_query_string
        try:
            found = await urlapp.client.exists(key)
        except Exception as e:
            logging.error(f"Exception : {e}")
            return JSONResponse(
                status_code=400,
                content={"Cause": "DB_UNAVAILABLE"},
            )        
        if found:
            return {"Add" : "Key Exists"}
        else:
            await urlapp.client.set(key, 1)
            logging.info(f"Key added {key}")
            return {"Add": "URL_ADD_SUCCESS"}
    else:
        return JSONResponse(
             status_code=400,
             content={"Cause": "Use Bulk API"},
        )

@urlapp.get("/urlinfo/1/{hostname_and_port}/{original_path_and_query_string}")
async def urlInfoLookup(hostname_and_port, original_path_and_query_string):

    # Enable for pytest until docker pytest developemnt is done
    # urlapp.client = StrictRedis(host="0.0.0.0", port="6379", db=0)

    req_stats.add_total_req_count()
    if not hostname_and_port or not original_path_and_query_string:
        return {"Cause" : "Bad_Request"}

    key = hostname_and_port + "/" + original_path_and_query_string

    try:
        found = await urlapp.client.exists(key)
    except Exception as e:
        logging.error(f"Exception : {e}")
        return JSONResponse(
            status_code=400,
            content={"Cause": "DB_UNAVAILABLE"},
        )
    if found:
        logging.info("Malware found", key)
        req_stats.add_malware_detected()
        return {"Cause": "MALWARE_DETECTED"}
    else:
        req_stats.add_malware_not_detected()
        return JSONResponse(
            status_code=404,
            content={"Cause": "MALWARE_NOT_DETECTED"},
        )

if __name__ == "__main__":
    logging.info(ip_addr, service_port)
    #registerUrlUpdateTimer("1")
    #registerUrlUpdater()   #For URL Update proxy service
    try:
        uvicorn.run(urlapp, host=ip_addr, port=service_port)
    except Exception as e:
        logging.error(f"Exception : {e}")


