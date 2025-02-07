import requests

# URL para obter o token
auth_url = "https://integration.systemsatx.com.br/Login"
auth_params = {
    "Username": "paulo_victor@ufms.br",
    "Password": "paulovictor999"
}

# Fazer a requisição para obter o token
auth_response = requests.post(auth_url, params=auth_params)

# Verificar se a autenticação foi bem-sucedida
if auth_response.status_code == 200:
    auth_data = auth_response.json()
    access_token = auth_data.get("AccessToken")

    # Configurar o cabeçalho com o token
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    # URL da segunda requisição
    tracker_url = "https://integration.systemsatx.com.br/Administration/Tracker/List"

    # Corpo da requisição
    payload = {
        "PropertyName": "TrackerIntegrationCode",
        "Condition": "Equal"
    }

    # Fazer a requisição POST
    tracker_response = requests.post(tracker_url, json=payload, headers=headers)

    # Verificar a resposta
    if tracker_response.status_code == 200:
        print("Resposta da requisição Tracker/List:")
        tracker_data = tracker_response.json()
        for item in tracker_data:
            print(f"IdTracker: {item.get('IdTracker')}, TrackedUnitType: {item.get('TrackedUnitType')}")
    else:
        print(f"Erro na requisição Tracker/List: {tracker_response.status_code}, {tracker_response.text}")
else:
    print(f"Erro na autenticação: {auth_response.status_code}, {auth_response.text}")
