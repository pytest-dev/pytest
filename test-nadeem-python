import requests

# Exposed secret: API key
API_KEY = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"  # Example secret key

def get_user_data(user_id):
    url = f"https://api.example.com/users/{user_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Unable to fetch data"}

if __name__ == "__main__":
    user_id = "12345"
    user_data = get_user_data(user_id)
    print(user_data)
