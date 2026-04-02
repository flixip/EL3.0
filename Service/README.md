# apimanager + codeline 开发手册（保姆级·最终版）
包名统一为**小写**：`apimanager`、`codeline`
全程无冗余代码、无自动识别、双框架可控、全自动生成前端接口

---

## 🔥 一句话核心总结
- `codeline`：**代码生成积木库**，告别手写缩进/分号/字符串拼接，模块化生成 TS/Python 代码
- `apimanager`：**全局单例 API 管理器**，FastAPI/Flask 双框架无缝切换，自动解析入参、统一响应、**全自动生成 TS 类型 + 请求函数**

---

## 🧱 一、codeline 代码生成器
### 1. 核心作用
专门解决**代码生成格式混乱**问题，通过类模块化搭建代码结构，自动处理缩进、空行、语法符号。

### 2. 核心积木类
| 类名                | 功能                          | 支持语言 |
|---------------------|-------------------------------|----------|
| `CodeGenerator`     | 代码生成总控制器（核心入口）| TS/Python |
| `CommentBlock`      | 单行注释                      | 通用     |
| `ImportBlock`       | 模块导入语句                  | 通用     |
| `InterfaceBlock`    | TS 接口 / 数据模型            | TS       |
| `FunctionBlock`     | 同步/异步函数                 | 通用     |
| `SingleLineBlock`   | 单行代码片段                  | 通用     |

### 3. 极简用法
```python
from codeline import CodeGenerator, CommentBlock, ImportBlock

# 1. 创建生成器（指定语言：ts / py）
gen = CodeGenerator(lang="ts")

# 2. 拼接代码积木
gen.add(CommentBlock("自动生成文件，禁止手动修改"))
gen.add(ImportBlock(module="axios", alias="axios"))

# 3. 生成格式化代码
code = gen.generate()
```

---

## 🚀 二、apimanager API 管理器（核心）
### 1. 核心能力
✅ 全局单例，全项目共享一个实例
✅ FastAPI / Flask **双框架无缝切换**
✅ 自动解析 GET/POST 入参，视图函数无框架侵入
✅ 统一响应体 + 全局异常捕获
✅ 基于 Pydantic 模型**全自动生成 TS 代码**
✅ 一键启动服务 + 热重载 + 自动更新 TS 文件

### 2. 核心规则（必看）
#### ① 入参规则（自动处理，无需手动写 request）
- `GET` 请求：自动获取 **url 查询参数** (`?id=1`)
- `POST` 请求：自动获取 **JSON 请求体**
- 入参必须用 `Pydantic BaseModel` 定义，自动校验

#### ② 出参规则（统一响应）
- 所有接口**自动包装**为 `StandardOutParams` 标准格式
- 格式：`{"status": 200, "msg": "请求成功", ...自定义数据}`
- 异常自动捕获，返回 `status=500` + 错误信息

#### ③ 视图函数规则（纯业务，无框架耦合）
```python
# 函数只接收 params 字典，返回普通字典即可
def 接口名(params: dict):
    return {"data": xxx}
```

#### ④ TS 自动生成逻辑
1. 扫描所有接口的**入参/出参 Pydantic 模型**
2. 自动转换为 **TS Interface 类型**
3. 自动生成 `axios` 异步请求函数
4. 每次启动服务**自动覆盖更新**

---

## 🔧 三、使用方式（两种模式，任选）
### 模式 1：极简模式（推荐）
**自动创建 APP，无需手动实例化 FastAPI/Flask**
```python
from apimanager import manager, BaseModel, Field

# --------------------------
# 1. 一键配置（指定框架）
# --------------------------
manager.setup(framework="fastapi")  # 切换 flask 只需改这里

# --------------------------
# 2. 定义入参模型（Pydantic）
# --------------------------
class UserQuery(BaseModel):
    id: int = Field(description="用户ID")
    name: str | None = Field(None, description="用户名")

# --------------------------
# 3. 定义接口（装饰器）
# --------------------------
@manager.route(
    url="/user",
    method="GET",
    in_params=UserQuery,  # 入参模型
    # out_params=xxx      # 可选：自定义出参模型
)
def get_user(params):
    # params 自动解析完成，直接用
    return {"data": {"id": params["id"], "name": params.get("name")}}

# --------------------------
# 4. 一键启动（热重载+自动生成TS）
# --------------------------
if __name__ == "__main__":
    manager.run(debug=True)
```

### 模式 2：自定义 APP 模式
传入自己创建的 FastAPI/Flask 实例，灵活配置
```python
from apimanager import manager
from fastapi import FastAPI

# 自定义APP
app = FastAPI(title="我的项目", version="1.0")

# 传入自定义APP + 指定框架
manager.setup(framework="fastapi", app=app)

# 接口编写...

if __name__ == "__main__":
    manager.run()
```

---

## 📌 四、装饰器 @manager.route 完整参数
```python
@manager.route(
    url: str,             # 接口地址（必填）
    method: str = "GET",  # 请求方法：GET/POST
    in_params = None,     # 入参 Pydantic 模型
    out_params = None     # 出参 Pydantic 模型（默认StandardOutParams）
)
```

---

## 📦 五、内置标准响应体
所有接口默认使用，无需手动编写：
```python
# 自动包含：status、msg，支持扩展自定义字段
class StandardOutParams(BaseModel):
    status: int = 200
    msg: str = "请求成功"
    model_config = {"extra": "allow"}
```

---

## ✨ 六、一键启动 run 函数
```python
manager.run(
    host="127.0.0.1",  # 主机
    port=8000,         # 端口
    debug=True         # 开发模式：热重载+自动生成TS
)
```
- `debug=True`：代码保存 → 服务自动重启 → TS 文件自动更新
- 自动生成 `api.ts` 文件到项目根目录

---

## 📝 七、完整 Flask 示例
```python
from apimanager import manager, BaseModel, Field

# 仅修改框架名，业务代码完全不变
manager.setup(framework="flask")

class UserQuery(BaseModel):
    id: int = Field(description="用户ID")

@manager.route("/user", method="GET", in_params=UserQuery)
def get_user(params):
    return {"data": {"id": params["id"]}}

if __name__ == "__main__":
    manager.run()
```

---

## 🧾 八、生成的 TS 文件效果（自动生成）
```typescript
// AUTO-GENERATED API
// 基于 Pydantic JSON Schema 自动生成
import axios from 'axios';

interface UserQuery {
    id: number; // 用户ID
    name?: string | null; // 用户名
}

// GET /user
async function get_userApi(params: UserQuery) {
    return axios.get<any>("/user", { params });
}
```

---

## ⚡ 九、速查清单（过目不忘）
1. **导入**：只用 `from apimanager import manager`
2. **配置**：`manager.setup(framework="fastapi/flask")`
3. **模型**：用 `BaseModel` 定义入参/出参
4. **接口**：`@manager.route()` 装饰器
5. **启动**：`manager.run()` 一键运行
6. **生成**：TS 文件**自动生成**，无需手动调用

---
