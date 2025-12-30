"""
HTTP 客户端工具

框架级内置工具示例。
"""

import json
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


async def http_get(
    url: str,
    headers: Optional[str] = None,
    timeout: int = 30,
) -> str:
    """
    执行 HTTP GET 请求
    
    Args:
        url: 请求 URL
        headers: 请求头（JSON 格式字符串）
        timeout: 请求超时（秒）
    
    Returns:
        JSON 字符串，包含响应信息
    """
    request_headers = {}
    if headers:
        try:
            request_headers = json.loads(headers)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid headers JSON format"})
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=request_headers)
            
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text[:5000],  # 限制内容长度
                "url": str(response.url),
            }
            
            return json.dumps(result, ensure_ascii=False)
    except httpx.TimeoutException:
        return json.dumps({"error": "Request timeout", "url": url})
    except httpx.RequestError as e:
        return json.dumps({"error": str(e), "url": url})


async def http_post(
    url: str,
    body: Optional[str] = None,
    headers: Optional[str] = None,
    timeout: int = 30,
) -> str:
    """
    执行 HTTP POST 请求
    
    Args:
        url: 请求 URL
        body: 请求体（JSON 格式字符串）
        headers: 请求头（JSON 格式字符串）
        timeout: 请求超时（秒）
    
    Returns:
        JSON 字符串，包含响应信息
    """
    request_headers = {"Content-Type": "application/json"}
    if headers:
        try:
            request_headers.update(json.loads(headers))
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid headers JSON format"})
    
    request_body = None
    if body:
        try:
            request_body = json.loads(body)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid body JSON format"})
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url,
                headers=request_headers,
                json=request_body,
            )
            
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text[:5000],  # 限制内容长度
                "url": str(response.url),
            }
            
            return json.dumps(result, ensure_ascii=False)
    except httpx.TimeoutException:
        return json.dumps({"error": "Request timeout", "url": url})
    except httpx.RequestError as e:
        return json.dumps({"error": str(e), "url": url})


