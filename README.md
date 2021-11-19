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
