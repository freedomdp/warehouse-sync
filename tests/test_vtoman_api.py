import requests

def test_vtoman_product_post():
    url = "http://localhost:8000/vtoman/products/CT0005"
    try:
        response = requests.post(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Content: {response.text}")

        if response.headers.get('content-type') == 'application/json':
            print(f"JSON Response: {response.json()}")
        else:
            print("Response is not in JSON format")
    except requests.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_vtoman_product_post()
