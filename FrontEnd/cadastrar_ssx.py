import requests

# Definição da URL de autenticação e credenciais fixas
url_login = "https://integration.systemsatx.com.br/Login"
params = {
    "Username": "paulo_victor@ufms.br",
    "Password": "paulovictor999"
}

# Fazendo a requisição POST para autenticação
response = requests.post(url_login, params=params)

# Verificando se a autenticação foi bem-sucedida
if response.status_code != 200:
    print(f"❌ Erro ao obter o token: {response.status_code}")
    print(response.text)
else:
    try:
        response_json = response.json()
        token = response_json.get("AccessToken")  # Pegando corretamente o AccessToken
        if not token:
            print("⚠ AccessToken não encontrado na resposta.")
        else:
            print("✅ Autenticação bem-sucedida!")

            # Cabeçalhos com o token de autenticação
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Solicitando os dados do SIMCard ao usuário
            iccid = input("Digite o ICCID do SIMCard: ").strip()
            apn_domain = input("Digite o APNDomain: ").strip()
            telefone_completo = input("Digite o telefone no formato 'CountryCallingCode + AreaCallingCode + PhoneNumber' (exemplo: 5567992733018): ").strip()

            # Separando os valores corretamente
            country_calling_code = telefone_completo[:2]  # Pegamos os primeiros 2 dígitos
            area_calling_code = telefone_completo[2:5]  # Pegamos os próximos 3 dígitos
            phone_number = telefone_completo[5:]  # Pegamos o restante como número do telefone

            # Construindo o payload correto para o SIMCard
            simcard_payload = {
                "ICCID": iccid,
                "APNDomain": apn_domain,
                "CountryCallingCode": country_calling_code,
                "AreaCallingCode": area_calling_code,
                "PhoneNumber": phone_number,
                "BillingCylcleEndDay": None,
                "Price": None,
                "MegabyteLimit": None,
                "PIN": None,
                "PUK": None
            }

            # Definição do endpoint correto para cadastrar o SIMCard
            simcard_url = "https://integration.systemsatx.com.br/Administration/SimCard/Insert"
            simcard_response = requests.post(simcard_url, json=simcard_payload, headers=headers)

            if simcard_response.status_code == 200:
                print(f"✅ SIMCard {iccid} cadastrado com sucesso!")
            else:
                # Captura o erro e verifica se o SIMCard já existe
                error_message = simcard_response.text
                if "ICCID already exists" in error_message:
                    print(f"⚠ O SIMCard {iccid} já está cadastrado. Pulando o cadastro e seguindo para o equipamento...")
                else:
                    print(f"❌ Erro ao cadastrar SIMCard {iccid}. Código: {simcard_response.status_code}")
                    print(simcard_response.text)  # Exibe a resposta de erro
                    exit()

            # Agora cadastramos o equipamento, usando o ICCID (cadastrado ou já existente)
            register_url = "https://integration.systemsatx.com.br/Administration/Tracker/Insert"

            # Solicitando os dados do equipamento ao usuário
            id_tracker = input("Digite o IdTracker: ").strip()
            tracker_template_code = input("Digite o TrackerTemplateIntegrationCode: ").strip()

            # Se o usuário inserir "RST", substituímos por "123"
            if tracker_template_code.upper() == "RST":
                tracker_template_code = "123"

            imei = input("Digite o IMEI (deixe em branco se não quiser enviar): ").strip()

            # Construindo o payload para cadastrar o equipamento
            payload = {
                "IdTracker": id_tracker,
                "TrackerTemplateIntegrationCode": tracker_template_code,
                "ICCID1": iccid  # **Usando o ICCID cadastrado ou já existente**
            }
            if imei:  # Adiciona IMEI apenas se não for vazio
                payload["IMEI"] = imei

            print(f"🔍 Enviando requisição para cadastrar o equipamento com payload: {payload}")

            # Enviando a requisição POST para cadastrar o equipamento
            register_response = requests.post(register_url, json=payload, headers=headers)

            # Verificando a resposta do cadastro do equipamento
            if register_response.status_code == 200:
                print(f"✅ Equipamento {id_tracker} cadastrado com sucesso com o SIMCard {iccid}!")
                print(register_response.json())  # Exibe a resposta JSON da API
            else:
                print(f"❌ Erro ao cadastrar equipamento. Código: {register_response.status_code}")
                print(register_response.text)  # Exibe a resposta de erro

    except ValueError:
        print("❌ Resposta não é um JSON válido.")
