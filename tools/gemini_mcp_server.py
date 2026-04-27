#!/usr/bin/env python3
"""Gemini MCP server for the restaurant-review project."""

import os
import google.generativeai as genai
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gemini")


def _model(model_name: str = "gemini-2.0-flash") -> genai.GenerativeModel:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")
    genai.configure(api_key=key)
    return genai.GenerativeModel(model_name)


@mcp.tool()
def ask_gemini(prompt: str) -> str:
    """Ask Gemini anything. Use for general-purpose queries."""
    return _model().generate_content(prompt).text


@mcp.tool()
def analyze_restaurant(name: str, genre: str, score: str, memo: str) -> str:
    """Analyze a restaurant and return a Japanese summary with highlights and suggestions.

    Args:
        name: Restaurant name.
        genre: Genre (e.g. イタリアン, 和食).
        score: Overall score string (e.g. "4.2 / 5.0").
        memo: Free-text review notes stored in the DB.
    """
    prompt = (
        "以下のレストランデータを分析し、特徴・おすすめポイント・改善点を"
        "日本語200字以内で簡潔に答えてください。\n"
        f"店名: {name}\nジャンル: {genre}\n総合スコア: {score}\nメモ: {memo}"
    )
    return _model().generate_content(prompt).text


@mcp.tool()
def suggest_tags(name: str, description: str) -> str:
    """Suggest genre and scene tags for a restaurant in JSON format.

    Args:
        name: Restaurant name.
        description: Any descriptive text about the restaurant.
    """
    prompt = (
        f"レストラン「{name}」の説明: {description}\n"
        "このレストランに合うジャンルタグとシーンタグを JSON で返してください。\n"
        '形式: {"genre": ["..."], "scene": ["..."]}'
    )
    return _model().generate_content(prompt).text


if __name__ == "__main__":
    mcp.run()