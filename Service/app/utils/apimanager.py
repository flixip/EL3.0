from pydantic import BaseModel, Field
from typing import Optional, Any, Literal
from pathlib import Path

from .codeline import (
    CodeGenerator, CommentBlock, ImportBlock,
    InterfaceBlock, FunctionBlock, SingleLineBlock
)

# 标准响应体
class StandardOutParams(BaseModel):
    status: int = Field(200)
    msg: str = Field("请求成功")
    model_config = {"extra": "allow"}

# API 管理器
class ApiManager:
    _instance: Optional["ApiManager"] = None

    def __init__(self):
        if hasattr(self, "initialized"): return
        self.file_path = None
        self.initialized = True
        self.framework: str = ""  
        self.api_list = []
        self.app = None

    # 单例
    @classmethod
    def getInstance(cls) -> "ApiManager":
        if not cls._instance:
            cls._instance = ApiManager()
        return cls._instance

    # ==============================================
    # ✅ 智能 setup：传app自动识别，不传自动创建
    # ==============================================
    def setup(self, framework: Literal["fastapi", "flask"] = "fastapi", app: Optional[Any] = None):
       
        if app:
            self.app = app

        else:
            # 不传app → 默认创建 FastAPI 实例
            if framework == "fastapi":
                from fastapi import FastAPI
                self.app = FastAPI(title="Auto API")
                self.framework = "fastapi"
            elif framework == "flask":
                from flask import Flask
                self.app = Flask(__name__)
                self.framework = "flask"
            else:
                raise ValueError("framework must be fastapi or flask")

        # 3. 自动注册所有接口
        for api in self.api_list:
            self._register_route(api)

        return self
        

    # 路由装饰器
    def route(self, url: str, method="GET", in_params=None, out_params=None):
        def decorator(func):
            info = {
                "url": url, "method": method,
                "view_func": func,
                "in_params": in_params,
                "out_params": out_params or StandardOutParams
            }
            self.api_list.append(info)
            if self.app: self._register_route(info)
            return func
        return decorator

    # 内部路由注册
    def _register_route(self, info):
        u, m, f = info["url"], info["method"], info["view_func"]
        if self.framework == "fastapi":
            self._reg_fastapi(u, m, f)
        else:
            self._reg_flask(u, m, f)

    def _reg_fastapi(self, url, method, func):
        from fastapi import Request
        async def ep(request: Request):
            try:
                p = await request.json() if method=="POST" else dict(request.query_params)
                result = func(*[p])
                return StandardOutParams(**result).model_dump()
            except Exception as e:
                return StandardOutParams(status=500, msg=str(e)).model_dump()
        self.app.add_api_route(path=url, endpoint=ep, methods=[method])

    def _reg_flask(self, url, method, func):
        from flask import request, jsonify
        import asyncio

        # 🔥 关键：必须起一个固定名字！不让 Flask 自动处理！
        endpoint = f"{method}_{url.replace('/', '_').strip('_')}"

        def ep():
            try:
                # 正确获取参数
                if method == "GET":
                    p = request.args.to_dict()
                else:
                    p = request.get_json(silent=True) or {}

                # ✅ 兼容无参/有参（用 *args 完美方案，不报错）
                result = func(**p)

                # 异步兼容
                if asyncio.iscoroutine(result):
                    result = asyncio.run(result)

                return jsonify(StandardOutParams(**result).model_dump())

            except Exception as e:
                return jsonify(StandardOutParams(status=500, msg=str(e)).model_dump())

        # 🔥 修复核心：必须指定 endpoint！！！
        self.app.add_url_rule(
            url,
            endpoint=endpoint,  # 👈 就是加了这一行，报错彻底消失
            view_func=ep,
            methods=[method]
        )

    # TS 自动生成
    def _get_ts_type(self, s):
        if "$ref" in s: return s["$ref"].split("/")[-1]
        if any(k in s for k in ["anyOf","oneOf"]): return "|".join(self._get_ts_type(x) for x in s.get("anyOf",s.get("oneOf",[])))
        if s.get("type")=="array": return self._get_ts_type(s.get("items",{}))+"[]"
        if "enum" in s: return "|".join(f'"{v}"'for v in s["enum"])
        return {"string":"string","integer":"number","number":"number","boolean":"boolean","object":"Record<string,any>"}.get(s.get("type"),"any")

    def generate_frontend_ts(self, save_path: str | Path = "api.ts"):
       
        gen = CodeGenerator(lang="ts")

        # 头部
        gen.add(
            CommentBlock("Auto-Generated API | 请勿手动修改"),
            ImportBlock(module="axios", alias="axios"),
            SingleLineBlock("")
        )

        # =========================
        # 收集模型
        # =========================
        models = {}
        for api in self.api_list:
            if api["in_params"]:
                models[api["in_params"].__name__] = api["in_params"]
            if api["out_params"]:
                models[api["out_params"].__name__] = api["out_params"]


        # 生成 Interface
        for name, model in models.items():
            schema = model.model_json_schema()
            required = schema.get("required", [])
            props = schema.get("properties", {})

            fields = {}
            for field, info in props.items():
                ts_type = self._get_ts_type(info)
                optional = field not in required
                desc = info.get("description", "")
                fields[field] = (ts_type, desc, optional)

            gen.add(
                InterfaceBlock(name=name, fields=fields),
                SingleLineBlock("")
            )


        # 生成 API 函数（用你写的 FunctionBlock！）
        for api in self.api_list:
            func_name = api["view_func"].__name__
            method = api["method"].lower()
            url = api["url"]
            in_param = api["in_params"]
            out_param = api["out_params"] or StandardOutParams

            in_type = in_param.__name__ if in_param else None
            out_type = out_param.__name__

            # 函数体（SingleLineBlock）
            body = []
            if method == "get":
                if in_type:
                    body.append(SingleLineBlock(f"return axios.get('{url}', {{ params }})"))
                else:
                    body.append(SingleLineBlock(f"return axios.get('{url}')"))
            else:
                if in_type:
                    body.append(SingleLineBlock(f"return axios.{method}('{url}', params)"))
                else:
                    body.append(SingleLineBlock(f"return axios.{method}('{url}', {{}})"))

            # 核心：FunctionBlock 生成！
            if in_type:
                func_block = FunctionBlock(
                    name=func_name,
                    params={"params": in_type},
                    return_type=f"Promise<{out_type}>",
                    body=body,
                    is_async=True
                )
            else:
                func_block = FunctionBlock(
                    name=func_name,
                    params={},
                    return_type=f"Promise<{out_type}>",
                    body=body,
                    is_async=True
                )

            gen.add(
                CommentBlock(f"{method.upper()} {url}"),
                func_block,
                SingleLineBlock("")
            )

        # 输出
        code = gen.generate()
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(code)
        return code

    # 一键 run
    def run(self, host="127.0.0.1", port=8000, debug=False,auto_save=True,ts_path: str | Path = "api.ts"):
        # 识别运行出口
        self.file_path = Path(__file__)
        if auto_save and ts_path: self.generate_frontend_ts(ts_path)
        print(f"✅ {ts_path} 已自动更新")
        if self.framework == "fastapi":
            import uvicorn
            if debug:
                uvicorn.run(f"{self.file_path.stem}:app", host=host, port=port, reload=debug)
            else:
                uvicorn.run(self.app, host=host, port=port, reload=debug)
        else:
            self.app.run(host=host, port=port, debug=debug)

