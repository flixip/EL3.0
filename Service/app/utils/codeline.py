from typing import Literal, List, Optional
from abc import ABC, abstractmethod

# ==============================================
# 目标语言类型别名
# ==============================================
Lang = Literal["py", "ts"]
"""
目标语言类型枚举，支持：
- "py": Python
- "ts": TypeScript
"""

# ==============================================
# 基类：CodeBlock（所有代码块的抽象父类）
# ==============================================
class CodeBlock(ABC):
    """
    所有代码块的抽象基类，定义了代码块的通用接口和行为。
    
    核心特性：
    - 统一缩进管理（4空格）
    - 统一换行控制
    - 抽象 trans() 方法，子类必须实现具体的代码生成逻辑
    
    使用方式：
    继承此类并实现 trans() 方法，即可创建新的代码块类型。
    """

    def __init__(self, indent: int = 0, trailing_newline: bool = True):
        """
        初始化代码块基类。
        
        Args:
            indent: 缩进层级，0 表示无缩进，1 表示 4 空格，以此类推
            trailing_newline: 是否在代码块末尾添加换行符，默认为 True
        """
        self.indent = indent
        self.trailing_newline = trailing_newline

    @abstractmethod
    def trans(self, lang: Lang) -> str:
        """
        核心抽象方法：根据目标语言生成代码字符串。
        
        所有子类必须实现此方法，定义具体的代码生成逻辑。
        
        Args:
            lang: 目标语言，"py" 或 "ts"
            
        Returns:
            生成的代码字符串
        """
        pass

    def _get_indent_str(self, lang: Lang) -> str:
        """
        内部辅助方法：获取缩进字符串。
        
        统一使用 4 空格缩进，根据 indent 层级计算最终缩进字符串。
        
        Args:
            lang: 目标语言（此方法不依赖语言，但保留参数以保持接口一致性）
            
        Returns:
            缩进字符串，例如 "    "（4空格）
        """
        return " " * (self.indent * 4)

# ==============================================
# 子类：CommentBlock（注释块）
# ==============================================
class CommentBlock(CodeBlock):
    """
    注释代码块，支持生成单行注释和多行注释。
    
    支持的语言特性：
    - Python: # 单行注释 / \"\"\" 多行注释 \"\"\"
    - TypeScript: // 单行注释 / /** 多行注释 */
    
    使用示例：
        # 单行注释
        single_comment = CommentBlock("这是单行注释")
        print(single_comment.trans("py"))  # 输出: # 这是单行注释
        
        # 多行注释
        multi_comment = CommentBlock("这是多行注释\\n支持换行", is_multiline=True)
        print(multi_comment.trans("ts"))  # 输出: /** ... */
    """

    def __init__(self, content: str, indent: int = 0, is_multiline: bool = False):
        """
        初始化注释块。
        
        Args:
            content: 注释内容
            indent: 缩进层级
            is_multiline: 是否为多行注释，默认为 False（单行注释）
        """
        super().__init__(indent)
        self.content = content
        self.is_multiline = is_multiline

    def trans(self, lang: Lang) -> str:
        """
        根据目标语言生成注释代码。
        
        Args:
            lang: 目标语言
            
        Returns:
            生成的注释代码字符串
        """
        indent = self._get_indent_str(lang)
        if lang == "py":
            if self.is_multiline:
                return f'{indent}"""\n{indent}{self.content}\n{indent}"""\n'
            else:
                return f"{indent}# {self.content}\n"
        elif lang == "ts":
            if self.is_multiline:
                return f"{indent}/**\n{indent} * {self.content}\n{indent} */\n"
            else:
                return f"{indent}// {self.content}\n"
        return ""

# ==============================================
# 子类：ImportBlock（导入块）
# ==============================================
class ImportBlock(CodeBlock):
    """
    导入代码块，支持生成各种形式的导入语句。
    
    支持的导入形式：
    - Python: import module / from module import item / import module as alias
    - TypeScript: import default from 'module' / import { item } from 'module'
    
    使用示例：
        # Python from import
        import_py = ImportBlock(module="pydantic", items=["BaseModel", "Field"])
        print(import_py.trans("py"))  # 输出: from pydantic import BaseModel, Field
        
        # TypeScript 命名导入
        import_ts = ImportBlock(module="vue", items=["ref", "reactive"])
        print(import_ts.trans("ts"))  # 输出: import { ref, reactive } from 'vue';
    """

    def __init__(
        self,
        module: str,
        items: Optional[List[str]] = None,
        alias: Optional[str] = None,
        indent: int = 0
    ):
        """
        初始化导入块。
        
        Args:
            module: 要导入的模块名
            items: 要从模块中导入的具体项列表（可选），例如 ["BaseModel", "Field"]
            alias: 导入别名（可选），例如 "pd" for pandas
            indent: 缩进层级
        """
        super().__init__(indent)
        self.module = module
        self.items = items or []
        self.alias = alias

    def trans(self, lang: Lang) -> str:
        """
        根据目标语言生成导入代码。
        
        Args:
            lang: 目标语言
            
        Returns:
            生成的导入代码字符串
        """
        indent = self._get_indent_str(lang)
        if lang == "py":
            if self.items:
                items_str = ", ".join(self.items)
                return f"{indent}from {self.module} import {items_str}\n"
            else:
                alias_str = f" as {self.alias}" if self.alias else ""
                return f"{indent}import {self.module}{alias_str}\n"
        elif lang == "ts":
            if self.items:
                items_str = ", ".join(self.items)
                return f"{indent}import {{ {items_str} }} from '{self.module}';\n"
            else:
                alias_str = self.alias or self.module
                return f"{indent}import {alias_str} from '{self.module}';\n"
        return ""

# ==============================================
# 子类：InterfaceBlock（接口/类定义块）
# ==============================================
class InterfaceBlock(CodeBlock):
    """
    接口/类定义代码块，支持生成 TypeScript Interface 和 Python Pydantic Model。
    
    核心特性：
    - 支持字段类型、描述、可选标记
    - 自动生成 JSDoc/Field 注释
    - TypeScript: export interface Name { ... }
    - Python: class Name(BaseModel): ...
    
    使用示例：
        fields = {
            "id": ("number", "用户ID", False),
            "name": ("string", "用户名", True),
            "age": ("number", "年龄", False)
        }
        interface = InterfaceBlock(name="User", fields=fields)
        print(interface.trans("ts"))  # 输出 TypeScript Interface
        print(interface.trans("py"))  # 输出 Python Pydantic Model
    """

    def __init__(
        self,
        name: str,
        fields: dict,
        indent: int = 0,
        base_classes: Optional[List[str]] = None
    ):
        """
        初始化接口/类定义块。
        
        Args:
            name: 接口/类名
            fields: 字段字典，格式为 {field_name: (type_str, description, is_optional)}
                    例如: {"id": ("number", "用户ID", False)}
            indent: 缩进层级
            base_classes: 基类列表（仅 Python 有效），默认为 ["BaseModel"]
        """
        super().__init__(indent)
        self.name = name
        self.fields = fields
        self.base_classes = base_classes or []

    def trans(self, lang: Lang) -> str:
        """
        根据目标语言生成接口/类定义代码。
        
        Args:
            lang: 目标语言
            
        Returns:
            生成的接口/类定义代码字符串
        """
        indent = self._get_indent_str(lang)
        code = ""

        if lang == "ts":
            code += f"{indent}export interface {self.name} {{\n"
            for field_name, (field_type, desc, is_optional) in self.fields.items():
                optional_mark = "?" if is_optional else ""
                if desc:
                    code += f"{indent}    /** {desc} */\n"
                code += f"{indent}    {field_name}{optional_mark}: {field_type};\n"
            code += f"{indent}}}\n"

        elif lang == "py":
            base_str = ", ".join(self.base_classes) if self.base_classes else "BaseModel"
            code += f"{indent}class {self.name}({base_str}):\n"
            for field_name, (field_type, desc, is_optional) in self.fields.items():
                if desc:
                    code += f'{indent}    {field_name}: {field_type} = Field(description="{desc}")\n'
                else:
                    code += f"{indent}    {field_name}: {field_type}\n"

        return code

# ==============================================
# 子类：FunctionBlock（函数块）
# ==============================================
class FunctionBlock(CodeBlock):
    """
    函数定义代码块，支持生成 TypeScript 和 Python 函数。
    
    核心特性：
    - 支持同步/异步函数
    - 支持参数类型注解
    - 支持返回值类型注解
    - 支持函数体嵌套其他 CodeBlock
    
    使用示例：
        body = [
            SingleLineBlock("const res = await axios.get('/user')"),
            SingleLineBlock("return res.data")
        ]
        func = FunctionBlock(
            name="getUser",
            params={"id": "number"},
            return_type="Promise<User>",
            body=body,
            is_async=True
        )
        print(func.trans("ts"))  # 输出 TypeScript 异步函数
    """

    def __init__(
        self,
        name: str,
        params: dict,
        return_type: Optional[str] = None,
        body: List[CodeBlock] = None,
        is_async: bool = False,
        indent: int = 0
    ):
        """
        初始化函数块。
        
        Args:
            name: 函数名
            params: 参数字典，格式为 {param_name: type_str}
                    例如: {"id": "number", "name": "string"}
            return_type: 返回值类型字符串（可选）
            body: 函数体代码块列表，元素为 CodeBlock 子类实例
            is_async: 是否为异步函数，默认为 False
            indent: 缩进层级
        """
        super().__init__(indent)
        self.name = name
        self.params = params
        self.return_type = return_type
        self.body = body or []
        self.is_async = is_async

    def trans(self, lang: Lang) -> str:
        """
        根据目标语言生成函数定义代码。
        
        Args:
            lang: 目标语言
            
        Returns:
            生成的函数定义代码字符串
        """
        indent = self._get_indent_str(lang)
        code = ""

        if lang == "ts":
            async_str = "async " if self.is_async else ""
            params_str = ", ".join([f"{k}: {v}" for k, v in self.params.items()])
            return_str = f": {self.return_type}" if self.return_type else ""
            code += f"{indent}export {async_str}function {self.name}({params_str}){return_str} {{\n"
            for block in self.body:
                block.indent = self.indent + 1
                code += block.trans(lang)
            code += f"{indent}}}\n"

        elif lang == "py":
            async_str = "async " if self.is_async else ""
            params_str = ", ".join([f"{k}: {v}" for k, v in self.params.items()])
            return_str = f" -> {self.return_type}" if self.return_type else ""
            code += f"{indent}{async_str}def {self.name}({params_str}){return_str}:\n"
            for block in self.body:
                block.indent = self.indent + 1
                code += block.trans(lang)

        return code

# ==============================================
# 子类：SingleLineBlock（单句代码块）
# ==============================================
class SingleLineBlock(CodeBlock):
    """
    单句代码块，用于生成单行代码语句。
    
    核心特性：
    - 自动根据语言添加分号（TypeScript 加分号，Python 不加）
    - 空内容时只输出换行，不生成多余分号
    
    使用示例：
        line_py = SingleLineBlock("print('Hello World')")
        print(line_py.trans("py"))  # 输出: print('Hello World')
        
        line_ts = SingleLineBlock("console.log('Hello World')")
        print(line_ts.trans("ts"))  # 输出: console.log('Hello World');
    """

    def __init__(self, content: str, indent: int = 0):
        """
        初始化单句代码块。
        
        Args:
            content: 代码内容字符串
            indent: 缩进层级
        """
        super().__init__(indent)
        self.content = content

    def trans(self, lang: Lang) -> str:
        """
        根据目标语言生成单句代码。
        
        Args:
            lang: 目标语言
            
        Returns:
            生成的单句代码字符串
        """
        indent = self._get_indent_str(lang)
        if not self.content.strip():
            return "\n"
        semicolon = ";" if lang == "ts" else ""
        return f"{indent}{self.content}{semicolon}\n"

# ==============================================
# 核心：CodeGenerator（代码生成器）
# ==============================================
class CodeGenerator:
    """
    统一代码生成器，负责管理和组合多个 CodeBlock，并最终生成完整代码文件。
    
    核心特性：
    - 统一管理所有代码块
    - 支持链式添加代码块
    - 按顺序生成完整代码
    - 支持 Python 和 TypeScript 两种语言
    
    使用示例：
        gen = CodeGenerator(lang="ts")
        gen.add(CommentBlock("AUTO-GENERATED CODE"))
        gen.add(ImportBlock(module="axios", alias="axios"))
        gen.add(InterfaceBlock(name="User", fields={...}))
        gen.add(FunctionBlock(name="getUser", ...))
        full_code = gen.generate()
        print(full_code)
    """

    def __init__(self, lang: Lang):
        """
        初始化代码生成器。
        
        Args:
            lang: 目标语言，"py" 或 "ts"
        """
        self.lang = lang
        self.blocks: List[CodeBlock] = []

    def add(self, block: CodeBlock,*args):
        """
        添加单个代码块。
        
        Args:
            block: CodeBlock 子类实例
            可以传多个代码块
        """
        self.blocks.append(block)
        self.blocks.extend(args)
        

    def add_all(self, blocks: List[CodeBlock]):
        """
        批量添加多个代码块。
        
        Args:
            blocks: CodeBlock 子类实例列表
        """
        self.blocks.extend(blocks)

    def generate(self) -> str:
        """
        生成完整代码字符串。
        
        按添加顺序遍历所有代码块，调用每个块的 trans() 方法，
        并将结果拼接成最终的完整代码。
        
        Returns:
            完整的代码字符串
        """
        code = ""
        for block in self.blocks:
            code += block.trans(self.lang)
        return code