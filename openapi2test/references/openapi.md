# OpenAPI 规范解析参考

## 支持的 OpenAPI 版本

- OpenAPI 3.0.0+
- OpenAPI 3.0.x
- OpenAPI 3.1.x

不支持 OpenAPI 2.x（Swagger 2.0），如需支持请先转换格式。

---

## 关键路径解析

### paths

```python
paths = {
    "/pet": {
        "post": {  # HTTP 方法
            "tags": ["pet"],  # 分组标签
            "summary": "Add a new pet to the store",
            "operationId": "addPet",
            "parameters": [...],
            "requestBody": {...},
            "responses": {...}
        }
    }
}
```

### components.schemas

```python
schemas = {
    "Pet": {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "format": "int64"},
            "name": {"type": "string", "example": "doggie"},
            "status": {"type": "string", "enum": ["available", "pending", "sold"]}
        },
        "required": ["name", "photoUrls"]
    }
}
```

### securitySchemes

```python
security_schemes = {
    "api_key": {
        "type": "apiKey",
        "name": "api_key",
        "in": "header"
    },
    "petstore_auth": {
        "type": "oauth2",
        "flows": {
            "implicit": {
                "authorizationUrl": "https://example.com/oauth/authorize",
                "scopes": {"read:pets": "Read pets", "write:pets": "Modify pets"}
            }
        }
    }
}
```

---

## 路径参数替换

当路径中有 `{param}` 时，测试函数需要接受对应参数：

```python
# /pet/{petId} -> test_get_pet_by_id(pet_id)
@pytest.mark.parametrize("pet_id", [1, 10, 100])
def test_get_pet_by_id(base_url, pet_id):
    response = requests.get(f"{base_url}/pet/{pet_id}")
```

---

## 请求体生成

根据 `requestBody.content` 的 media type 生成请求体：

| Media Type | 生成方式 |
|------------|---------|
| `application/json` | `requests.post(url, json=payload)` |
| `application/x-www-form-urlencoded` | `requests.post(url, data=payload)` |
| `multipart/form-data` | `requests.post(url, files=files)` |
| `application/octet-stream` | `requests.post(url, data=binary_data)` |

---

## 响应断言策略

### 状态码断言
```python
assert response.status_code == 200  # 成功
assert response.status_code == 400  # 客户端错误
assert response.status_code == 404  # 未找到
```

### 响应体断言
```python
# 基于 schema 属性
data = response.json()
assert "id" in data
assert data["name"] == "expected"
assert data["status"] in ["available", "pending", "sold"]
```

### 数组响应断言
```python
assert isinstance(response.json(), list)
if response.json():
    item = response.json()[0]
    assert "id" in item
```

---

## 安全认证处理

### apiKey
```python
# header 方式
headers = {"api_key": "your-api-key"}

# query 方式
params = {"api_key": "your-api-key"}
```

### OAuth2
```python
# 使用环境变量或 mock token
ACCESS_TOKEN = os.getenv("OAUTH_TOKEN", "mock-token")
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
```

### 无认证
```python
# 公开接口，无需认证
response = requests.get(url)
```
