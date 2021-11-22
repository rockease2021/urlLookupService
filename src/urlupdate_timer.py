import os
import time
from  threading import Timer
from aredis import StrictRedis
import asyncio
import logging


interval     = 600 #10min timer
redis_ip     = os.getenv('DATABASE') if os.getenv('DATABASE') else "localhost"
redis_port   = os.getenv('REDIS_PORT') if os.getenv('REDIS_PORT') else "6379"
file_path    = os.getenv('FILE_PATH') if os.getenv('FILE_PATH') else "/Users/rmuthusamy/Downloads/redis/blocklist.txt" # Predifned Mount path
runflag      = "1" #To control start/stop

logging.basicConfig(filename='apptimer.log', level=logging.ERROR)

async def urlUpdateTimer():
    redis_db = StrictRedis(host=redis_ip, port=redis_port, db=0)

    if not file_path:
        loggin.info("Mount path is empty")
        return

    count = 0
    print(file_path)
    try:
        block_list_file = open(file_path, 'r')
    except FileNotFoundError:
        logging.info("File not found")
        return
    except:
        logging.info("Unknown error")
        return
    else:
        for line in block_list_file:
            key = line.rstrip('\n')
            if  await redis_db.exists(key):
                logging.info(f"existing item: {key}")
            else:
                await redis_db.set(key, 1)
                logging.info(f"new: {key}")
                count += 1
        logging.info("Bulk Add success - count :",count)
        return
    return

def registerUrlUpdateTimer(flag):
    if  flag == "1":
        global runflag
        logging.info("\n timer running..", time.ctime())
        asyncio.run(urlUpdateTimer())
        Timer(interval, registerUrlUpdateTimer, args=runflag).start()
    else:
        runflag = "0"
        Timer(interval, registerUrlUpdateTimer, args=runflag).cancel()
        logging.info("timer stopped")


