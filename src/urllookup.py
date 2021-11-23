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

#For debugging
total_req_count      = 0
malware_detected     = 0
malware_not_detected = 0
total_failed_req     = 0

redis_ip     = os.getenv('DATABASE') if os.getenv('DATABASE') else "redis"
redis_port   = os.getenv('REDIS_PORT') if os.getenv('REDIS_PORT') else "6379"
service_port = os.getenv('APP_PORT') if os.getenv('APP_PORT') else "8090"
ip_addr      = os.getenv('IP') if os.getenv('IP') else "0.0.0.0"

@urlapp.on_event("startup")
async def startup():
    logging.debug("Starting the URL Lookup Service")
    urlapp.client = StrictRedis(host=redis_ip, port=redis_port, db=0)

@urlapp.on_event("shutdown")
async def shutdown():
    logging.debug("Closing the application")
    #registerUrlUpdateTimer("0")


@urlapp.get("/help")
def helper():
    return {"urllookup": "/urlinfo/1/{hostname_and_port}/{original_path_and_query_string}"}

@urlapp.get("/stats")
def urlappStats():
    logging.debug("Get Statistics")
    logging.info(f"Total reqs :{total_req_count} Total Failed req: {total_failed_req}"
                 f"Total Malware detected: {malware_detected}, Total Good Req : {malware_not_detected}")

    return {"Total Requests": str(total_req_count + total_failed_req),
            "Malwares_detected" : str(malware_detected),
            "Malwares_not_detected" : str(malware_not_detected)}

@urlapp.exception_handler(StarletteHTTPException)
async def httpExceptionHanlder(Request, exc):
    global total_failed_req
    total_failed_req += 1
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
        if await urlapp.client.exists(key):
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
    global total_req_count
    global malware_detected
    global malware_not_detected

    # Enable for pytest until docker pytest developemnt is done
    # urlapp.client = StrictRedis(host="0.0.0.0", port="6379", db=0)

    total_req_count += 1
    if not hostname_and_port or not original_path_and_query_string:
        return {"Cause" : "Bad_Request"}
    found = 0
    found = await urlapp.client.exists(hostname_and_port + "/" + original_path_and_query_string)
    if found:
        logging.info("Malware found",hostname_and_port + "/" + original_path_and_query_string)
        malware_detected += 1
        return {"Cause": "MALWARE_DETECTED"}
    else:
        malware_not_detected += 1
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


