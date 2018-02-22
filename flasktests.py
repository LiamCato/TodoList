import unittest
import requests

class TestAPIFunctions(unittest.TestCase):
    
    def test_login(self):
        login_url = "http://localhost:5000/api/sessiontoken"
        login_data = {"Username":"Testuser","Password":"Secretcode"}
        self.assertTrue("SessionToken" in requests.post(login_url,json=login_data).cookies)

    def test_logout(self):
        url = "http://localhost:5000/api"
        login_url = url + "/sessiontoken"
        todo_url = url + "/todo"
        login_data = {"Username":"Testuser","Password":"Secretcode"}
        session = requests.session()
        session.post(login_url,json=login_data)
        self.assertTrue("SessionToken" in session.cookies and session.cookies["SessionToken"] != "")
        session.put(login_url)
        self.assertTrue("SessionToken" not in session.cookies)
        response = session.get(todo_url)
        self.assertEqual(response.status_code, 401)

    def test_create(self):
        url = "http://localhost:5000/api"
        login_url = url + "/sessiontoken"
        todo_url = url + "/todo"
        login_data = {"Username":"Testuser","Password":"Secretcode"}
        session = requests.session()
        session.post(login_url,json=login_data)
        test_data = {"Description": "An item on my to do list","Completed":False}
        response = session.post(todo_url, json=test_data)
        self.assertTrue("Id" in response.json() and isinstance(response.json()["Id"],str))

    def test_get(self):
        url = "http://localhost:5000/api"
        login_url = url + "/sessiontoken"
        todo_url = url + "/todo"
        login_data = {"Username":"Testuser","Password":"Secretcode"}
        test_data = {"Description": "An item on my to do list","Completed":False}
        session = requests.session()
        session.post(login_url,json=login_data)
        session.post(todo_url,json=test_data)
        response = session.get(todo_url).json()
        self.assertTrue(isinstance(response,list))
        self.assertGreaterEqual(len(response),1)
        compare = response[0]
        compare.pop("Id")
        self.assertDictEqual(test_data,compare)

    def test_update(self):
        url = "http://localhost:5000/api"
        login_url = url + "/sessiontoken"
        todo_url = url + "/todo"
        login_data = {"Username":"Testuser","Password":"Secretcode"}
        update_data = {"Description": "A different description","Completed":True}
        session = requests.session()
        session.post(login_url,json=login_data)
        response = session.get(todo_url).json()
        id = response[0].pop("Id")
        self.assertTrue(isinstance(id,str))
        updated = session.put(todo_url +"/" + id,json=update_data).json()
        updated.pop("Id")
        self.assertDictEqual(updated,update_data)

    def test_delete(self):
        url = "http://localhost:5000/api"
        login_url = url + "/sessiontoken"
        todo_url = url + "/todo"
        login_data = {"Username":"Testuser","Password":"Secretcode"}
        session = requests.session()
        session.post(login_url,json=login_data)
        response = session.get(todo_url).json()
        self.assertTrue(isinstance(response,list))
        self.assertGreaterEqual(len(response),1)
        id = response[0].pop("Id")
        self.assertTrue(isinstance(id,str))
        del_response = session.delete(todo_url + "/" + id)
        self.assertEqual(del_response.status_code, 203)
        get_check = session.get(todo_url).json()
        if len(get_check) != 0:
            for item in get_check:
                self.assertNotEqual(item["Id"],id)


if __name__ == '__main__':
    unittest.main()
