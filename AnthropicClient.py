"""
Anthropic Claude API 异步客户端封装
支持 Claude 3.5, Claude 4.0, Claude 4.5 模型
兼容 FastAPI 异步框架
"""
import asyncio
import json
from typing import AsyncGenerator, List, Dict, Optional, Any
import httpx


class AnthropicClient:
    """Anthropic API 异步客户端"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com",
        support_system_prompt: bool = None
    ):
        """
        初始化 Anthropic 客户端

        :param api_key: Anthropic API 密钥
        :param base_url: API 基础地址（支持官方 API 或第三方代理）
        :param support_system_prompt: 是否支持 system prompt（None=自动检测）
        """
        self.api_key = api_key
        # 确保 base_url 不包含尾部斜杠
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        # system prompt 支持状态：None=未检测，True=支持，False=不支持
        self.support_system_prompt = support_system_prompt

    def _convert_messages(
        self,
        messages: List[Dict[str, str]],
        use_system_as_message: bool = False
    ) -> tuple[Optional[str], List[Dict[str, str]]]:
        """
        转换 OpenAI 格式的消息为 Anthropic 格式

        Anthropic 要求：
        - system 消息单独作为参数（如果API支持）
        - messages 数组只包含 user 和 assistant 消息
        - 第一条消息必须是 user
        - 消息必须严格交替（user -> assistant -> user）

        :param messages: OpenAI 格式的消息列表
        :param use_system_as_message: 是否将 system 作为普通消息（用于不支持 system 参数的API）
        :return: (system_prompt, anthropic_messages)
        """
        system_prompt = None
        anthropic_messages = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            if role == "system":
                # 提取 system 消息
                system_prompt = content
            elif role in ["user", "assistant"]:
                # 保留 user 和 assistant 消息
                anthropic_messages.append({
                    "role": role,
                    "content": content
                })

        # 如果不支持 system 参数，将其合并到第一条 user 消息
        if use_system_as_message and system_prompt:
            if anthropic_messages and anthropic_messages[0]["role"] == "user":
                # 合并到第一条 user 消息
                anthropic_messages[0]["content"] = f"{system_prompt}\n\n{anthropic_messages[0]['content']}"
            else:
                # 作为第一条 user 消息
                anthropic_messages.insert(0, {"role": "user", "content": system_prompt})
            system_prompt = None  # 清空，不作为单独参数

        # 确保消息列表不为空
        if not anthropic_messages:
            raise ValueError("消息列表不能为空")

        # 确保第一条消息是 user（Anthropic 要求）
        if anthropic_messages[0]["role"] != "user":
            anthropic_messages.insert(0, {"role": "user", "content": "开始对话"})

        # 验证消息交替（Anthropic 严格要求）
        # 移除连续的相同角色消息，只保留最后一条
        cleaned_messages = []
        for msg in anthropic_messages:
            if not cleaned_messages or cleaned_messages[-1]["role"] != msg["role"]:
                cleaned_messages.append(msg)
            else:
                # 合并连续的相同角色消息
                cleaned_messages[-1]["content"] += "\n\n" + msg["content"]

        # 确保最后一条是 user 消息（因为我们需要 assistant 的回复）
        if cleaned_messages and cleaned_messages[-1]["role"] == "assistant":
            cleaned_messages.append({"role": "user", "content": "继续"})

        return system_prompt, cleaned_messages

    async def send_message_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.8,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        debug: bool = False,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        异步流式发送消息到 Anthropic API

        :param model: 使用的模型名称，例如 "claude-sonnet-4-20250514"
        :param messages: 消息列表（OpenAI 格式会自动转换）
        :param max_tokens: 最大生成 tokens 数
        :param temperature: 温度参数，控制随机性
        :param top_p: 核采样参数
        :param top_k: 采样候选数
        :param debug: 是否输出调试信息
        :yield: 流式响应块
        """
        # 根据支持情况决定是否使用 system 参数
        # 如果明确知道不支持，或者未知但检测到过错误，则合并到消息中
        use_system_as_message = (self.support_system_prompt == False)

        # 转换消息格式
        system_prompt, anthropic_messages = self._convert_messages(
            messages,
            use_system_as_message=use_system_as_message
        )

        if debug:
            print(f"[DEBUG] Support system prompt: {self.support_system_prompt}")
            print(f"[DEBUG] System prompt: {system_prompt}")
            print(f"[DEBUG] Anthropic messages: {anthropic_messages}")

        # 构建请求体
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        # 如果有 system prompt 且API支持，添加到请求中
        if system_prompt and not use_system_as_message:
            payload["system"] = system_prompt

        # 添加可选参数
        if top_p is not None:
            payload["top_p"] = top_p
        if top_k is not None:
            payload["top_k"] = top_k

        if debug:
            print(f"[DEBUG] Request payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        # 发送异步请求
        try:
            async with httpx.AsyncClient(timeout=120.0) as http_client:
                async with http_client.stream(
                    "POST",
                    f"{self.base_url}/v1/messages",
                    headers=self.headers,
                    json=payload,
                ) as response:
                    if debug:
                        print(f"[DEBUG] Response status: {response.status_code}")
                        print(f"[DEBUG] Response headers: {dict(response.headers)}")

                    # 检查错误
                    if response.status_code >= 400:
                        error_body = await response.aread()
                        error_text = error_body.decode('utf-8')
                        if debug:
                            print(f"[DEBUG] Error response: {error_text}")

                        # 检测是否是 system prompt 不支持的错误
                        if "system prompt not allowed" in error_text.lower():
                            if debug:
                                print("[DEBUG] 检测到 API 不支持 system prompt，自动重试...")
                            # 标记为不支持
                            self.support_system_prompt = False
                            # 递归重试（这次会将 system 合并到消息中）
                            async for chunk in self.send_message_stream(
                                model=model,
                                messages=messages,
                                max_tokens=max_tokens,
                                temperature=temperature,
                                top_p=top_p,
                                top_k=top_k,
                                debug=debug
                            ):
                                yield chunk
                            return  # 重试成功，退出当前函数

                        raise httpx.HTTPStatusError(
                            f"HTTP {response.status_code}: {error_text}",
                            request=response.request,
                            response=response
                        )

                    response.raise_for_status()

                    # 流式处理 SSE 响应
                    async for line in response.aiter_lines():
                        line = line.strip()

                        # 跳过空行和注释行
                        if not line or line.startswith(":"):
                            continue

                        # 解析 SSE 格式
                        if line.startswith("data: "):
                            data_str = line[6:]  # 移除 "data: " 前缀

                            # 检查是否结束
                            if data_str == "[DONE]":
                                break

                            try:
                                data = json.loads(data_str)
                                if debug:
                                    print(f"[DEBUG] Received chunk: {data.get('type', 'unknown')}")
                                yield data
                            except json.JSONDecodeError as e:
                                if debug:
                                    print(f"[DEBUG] JSON decode error: {e}, data: {data_str[:100]}")
                                continue
        except httpx.HTTPError as e:
            if debug:
                print(f"[DEBUG] HTTP error: {e}")
            raise


async def anthropic_stream_to_sse(
    client: AnthropicClient,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.8,
    max_tokens: int = 4096,
    debug: bool = False,
) -> AsyncGenerator[str, None]:
    """
    将 Anthropic 流式响应转换为与 OpenAI 兼容的 SSE 格式

    :param client: AnthropicClient 实例
    :param model: 模型名称
    :param messages: 消息列表
    :param temperature: 温度参数
    :param max_tokens: 最大token数
    :param debug: 是否输出调试信息
    :yield: SSE 格式的字符串
    """
    try:
        async for chunk in client.send_message_stream(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            debug=debug,
        ):
            # 解析 Anthropic 的流式响应
            event_type = chunk.get("type")

            if event_type == "content_block_delta":
                # 内容增量更新
                delta = chunk.get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    if text:
                        payload = json.dumps({"token": text}, ensure_ascii=False)
                        yield f"data: {payload}\n\n"
                        await asyncio.sleep(0.001)

            elif event_type == "message_stop":
                # 消息结束
                yield 'data: {"event":"[DONE]"}\n\n'
                break

    except httpx.HTTPError as e:
        error_msg = f"Anthropic API 错误: {str(e)}"
        if debug:
            print(f"[DEBUG] {error_msg}")
        yield f"data: {json.dumps({'error': error_msg})}\n\n"
    except Exception as e:
        error_msg = f"未知错误: {str(e)}"
        if debug:
            print(f"[DEBUG] {error_msg}")
            import traceback
            traceback.print_exc()
        yield f"data: {json.dumps({'error': error_msg})}\n\n"