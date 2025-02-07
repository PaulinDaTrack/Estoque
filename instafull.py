import requests

url = "https://ws.fulltrack2.com/trackers/all"
headers = {
    "apikey": "f8c496428711c7dea7347ea76ffa4733cdd9c406",
    "secretkey": "3a7e6572ccdedb8f8e0996f9ecca8bf9d017b4dc"
}

response = requests.get(url, headers=headers)

try:
    data = response.json()  # Converte para JSON

    # Descobre a chave que contém a lista de dados
    key_for_list = next((key for key in data if isinstance(data[key], list)), None)

    if key_for_list:
        trackers = data[key_for_list]  # Pega a lista correta

        for item in trackers:
            ras_ras_id_aparelho = item.get("ras_ras_id_aparelho", "N/A")
            ras_ras_cli_id = item.get("ras_ras_cli_id", "N/A")
            print(f"ID: {ras_ras_id_aparelho}, Status: {ras_ras_cli_id}")
    else:
        print("Erro: Não foi encontrada uma lista dentro do JSON.")

except requests.exceptions.JSONDecodeError:
    print("Erro: A resposta não está em formato JSON válido.", response.text)
