import time

def test_urlapp_200OK(test_app):
    print(f"\n{time.ctime()} :- URL lookup 200OK Test \n")
    resp = test_app.get("/urlinfo/1/hostname_and_port/original_path_and_query_string")
    assert resp.status_code == 200
    assert resp.json() == {"Cause" : "MALWARE_DETECTED"}

def test_urlupdate(test_app):
    print(f"{time.ctime()} :- URL Update 200OK Test\n")
    resp = test_app.post("/urlupdate/1/")
    assert resp.status_code == 400

def test_url_404(test_app):
    print(f"{time.ctime()} :- URL lookup 404 Test\n")
    resp = test_app.get("/urlinfo/1/hostname_and_port/o")
    assert resp.status_code == 404 
    assert resp.json() == {"Cause" : "MALWARE_NOT_DETECTED"}

def test_url_400(test_app):
    print(f"{time.ctime()} :- URL lookup 400 Test\n")
    resp = test_app.get("/urlinf")
    assert resp.status_code == 400
    assert resp.json() == {"Cause" : "INVALID_URL_REQUESTED"}

def test_1K_url(test_app):
    n = 1000 
    print(f"{time.ctime()} :- URL lookup 2K Test\n")
    for i in range(1,n):
        resp = test_app.get("/urlinfo/1/hostname_and_port/original_path_and_query_string")
        assert resp.status_code == 200
        assert resp.json() == {"Cause" : "MALWARE_DETECTED"}

    for i in range(1,n):
        resp = test_app.get(f"/urlinfo/1/hostname_port/original_path_and_query_string{i}")
        assert resp.status_code == 404
        assert resp.json() == {"Cause" : "MALWARE_NOT_DETECTED"} 
    print(time.ctime())
