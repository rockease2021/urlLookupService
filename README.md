# URL Lookup Service   

# Requirements 

1. Design a HTTP proxy that is scanning traffic looking for malware URL's.  This proxy asks a service that maintains several databases of malware URL's if the resource being requested is known to contain malware. Implement a web service to process the GET requests where the caller passes in a URL and the service responds with some information about that URL. These lookups are blocking users from accessing the URL until the caller receives a response from your service.

       GET Request:-
          GET /urlinfo/1/{hostname_and_port}/{original_path_and_query_string}

   The product should include:-

    a.  Necessary documentation for us to set up the service ourselves on EC2/Vagrant/Docker or similar system of your choosing.
  
    b.  GET response structure
  
    c.  Expected to handle thousands of requests per second
  
    d.  Unit test framework

2. Performance/Scale related requirements 

    a. The size of the URL list could grow infinitely, how might you scale this beyond the memory capacity of your single host?
   
    b. How to handle if the number of requestes exceed the capacity of the initial solution. 
   
    c. Update new URL - 5 thousand URLs a day with updated arriving every 10 minutes 



# Design

 ![URL_Lookiup_Design](https://user-images.githubusercontent.com/94652016/142744898-401bb599-aacd-42f8-bcb0-fc4550114f7e.png)


# Load Balancer:
   
   To load balance the HTTP Requests to the configured pool of Url Lookup services. Based on the need, We can spin up more URL lookup service intances to handle the scale requirements. This should help to handle the situation where the number of requests exceeds the capacity of the initial solution.    
   
   The design will include master and standby loadbalancer for the High availablity.
   
   The plan is to use HA Proxy Loadbalancer for load-balancing. Since the use case is to load balance the requests to the backend URL lookup web service, I prefer HAParoxy over Nginx.    
    We can even have a rate limit feature enabled on the load balancer to handle the burst of requests that exceed over Loadbalancer's performance. 
   
   Performance Number:
       HAProxy Forwards Over 2 Million HTTP Requests per Second on a Single Arm-based AWS Graviton2 Instance(64Core). 
       
   For implementation - I have used one HAproxy instance to talk to two backend lookup service instances.
       
# URL Lookup Proxy:

   The URL Lookup service proxy runs in an Asychoronus mode to handle the requests. This module queries the database to check whether the requested URL is legit or malware.
   To meet the performance requirements, I am using the FastAPI web framework with uvicorn to run a web service in an asycn mode. 
   
   Reason to Select FAST API:
       High performance with async support, can be compared with Golang.
       Easy to connect with redisDB
       Supports OpenAPI/SwaggerUI and JSON
   
              GET Request:-
                 GET /urlinfo/1/{hostname_and_port}/{original_path_and_query_string}
              
              Response:-
              
              The resposne structure contains Cause and Cause Value
                     Status code: 
                     Body : {Cause : Cause Code}
              
              
                  200 OK: The requested URL is a Malware
                     Body:
                     content={"Cause" : "MALWARE_DETECTED"}
                  404 : Malware not Detected (i.e The URL entry is not present in the Database)
                      content={"Cause": "MALWARE_NOT_DETECTED"}
                  400 : Requested URL is invalid or Request messages doesn't contain enough information to lookup
                      content={"Cause": "INVALID_URL_REQUESTED"}

# Redis DB:

   The URL datastore was designed with a redis cluster of 1 Leader/Master and "n" non-leader, So that we can provide HA for the data and the lookup will be faster. 
   
   Reasons to choose the Redis DB:
        It supports persistence
        In-memory database for faster lookups. 
        Redis provides both HA and Sharding, This will help to scale the database when the list grows.
        
   Redis DB should help to handle the infinite growth of blacklisted URLs.
   
   The plan is to write the URLs in the master DB and let it sync to all the others members in the cluster. This should help to separate out the datapath and control path (URL updater service).
   
   In the future, We can introduce a local cache in each URL lookup proxy instance to speed up the lookup time. May be a LRU cache. but we need to make sure data    is consistent across the DB and cache. 
   If needed, We can implement a timeout based keys to retire the old values in the DB. 
   
# URL Updater:
   
   As per the requirement, The URL update service should run for every 10mins to update the URLs. There are multiple ways to handle this requirement. I am proposing two methods. 
   
   1. Create a URL Update web service that listens on the mentioned IP/Port for the URL request POST API. once it receives the request, based on the POST API structure, it will act on it. 

              POST API:
              
             1. Bulk update :-  /urlupdate/1/bulk/{filename}
             2. Single Update :- /urlupdate/1/single/{hostname_and_port}/{original_path_and_query_string}

     For Bulk update - Mount location should be configured to access the file to read and load it into the DB. 
  
   2. Timer based approach. The timer will run for the configured time (10min) to access the mount location to update the URL lists. 

   In the future, We can add the file integrity checks on the mounted file to make sure it is not corrupted.

   3. Corn job -  To schedule a job for every 10min to run the python script. The script will follow the same model as #2 to load the url lists on RedisDB. 


# Setup Documentation 
              
              To launch a containers:
              
              sudo /usr/local/bin/docker-compose -f docker-compose.yaml up --build
              
              This will launch a two webservices, one HA proxy and one Redis DB for the testing.
              Please change the IP addresses based on the environment
              
              To test:
              
              curl http://0.0.0.0:80/urlinfo/1/hostname_and_port/original_path_and_query_string
              Ouput: 200 OK {"Cause":"MALWARE_DETECTED"}
              

# Unit test
   Please find the attached screen shots in unittest folder. 
   UT framework - 
        I have used pytest to test the webservice. Still this needs to be improved to handle all the modules and corner cases.

# Performance / Scale
   HAProxy can support 2Millon Requests per second.
   Redis can handle 100K lookups per second.
   Web Proxy service - AWS EC2 (1GB RAM, 1vCPU) - 5K rps with the available test setup

# API

![UrlLookup_API](https://user-images.githubusercontent.com/94652016/142819629-0c870c4e-ce2a-48eb-a2c1-321cd8e3d559.png)

![urlupdate_API](https://user-images.githubusercontent.com/94652016/142819662-84fbad7e-ee88-47b8-b28a-94b46f469fa5.png)


