# Plano de Testes e Validação de Requisitos

Os procedimentos de validação do projeto, com resultado obtido, são os que seguem:

| ID | Módulo / Escopo | Cenário de Teste | Procedimento/requisição | Resultado / Retorno |
|---|---|---|---|---|
| **01** | **Infraestrutura Docker** | Inicialização e orquestração dos containers | `docker compose up -d --build` e `docker compose ps`. | Todos os serviços entram em funcionamento (`Up` / `healthy`). |
| **02** | **Simulador -> MQTT** | Publicação periódica com autenticação e TLS | `docker compose logs -f simulator`. | O simulador publica payloads JSON nos tópicos `/{prefix}/sensores/sensor_XX/data` no intervalo definido. |
| **03** | **Consumidor -> Banco** | Ingestão e persistência temporal ponta a ponta | `SELECT * FROM temperature_data ORDER BY time DESC LIMIT 5;`. | Os registros publicados no MQTT aparecem na base de dados com os dados correspondentes. |
| **04** | **Consumidor (Resiliência)** | Tratamento de payload malformado ou incompleto | Publicar (manualmente) uma mensagem com JSON inválido (`{invalido}`) | O consumidor registra um aviso/erro controlado nos logs e descarta a mensagem |
| **05** | **API REST (Saúde)** | Diagnóstico de conectividade da API com o banco |  `GET /health`. | `200 OK` e JSON indicando `"status": "healthy"` e `"database": "ok"`. |
| **06** | **API REST (Consulta)** | Listagem e última leitura por sensor | `GET /api/sensors` e em seguida `GET /api/sensors/sensor_01/latest`. | `200 OK`, os IDs ativos, o valor mais recente de `temperature` e a contagem total de registros (`total_records`). |
| **07** | **API REST (Filtros)** | Consulta histórica com janela de tempo e paginação | `GET /api/sensors/sensor_01/data?limit=5&order=asc`. | `200 OK` e 5 registros em ordem cronologicamente crescente. |
| **08** | **API REST (Erro 404)** | Consulta de dispositivo inexistente | `GET /api/sensors/sensor_99/latest`. | `404 Not Found` e mensagem informando que o sensor não foi encontrado. |
