import requests

# URL da API
url = "https://ws.fulltrack2.com/trackers/save"

# Credenciais
headers = {
    "apikey": "f8c496428711c7dea7347ea76ffa4733cdd9c406",
    "secretkey": "3a7e6572ccdedb8f8e0996f9ecca8bf9d017b4dc",
    "Content-Type": "application/json"
}

# Solicitando dados do rastreador ao usuário
ras_ras_id_aparelho = input("Digite o ID do aparelho (hexadecimal): ")
ras_ras_prd_id = int(input("Digite o ID do produto: "))
ras_ras_chip = int(input("Digite o ID do chip: "))
ras_ras_imei = input("Digite o IMEI do equipamento: ")

# Dados do rastreador a ser criado
data = {
    "ras_ras_id_aparelho": ras_ras_id_aparelho,
    "ras_ras_prd_id": ras_ras_prd_id,
    "ras_ras_chip": ras_ras_chip,
    "ras_ras_linha": None,  # Número da linha sempre nulo
    "ras_ras_imei": ras_ras_imei
}

# Fazendo a requisição PUT
response = requests.put(url, json=data, headers=headers)

# Exibindo a resposta
print("Status Code:", response.status_code)
print("Response:", response.json())
