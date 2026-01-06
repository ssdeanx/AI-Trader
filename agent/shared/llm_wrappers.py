import json
from typing import Optional
from langchain_openai import ChatOpenAI

class DeepSeekChatOpenAI(ChatOpenAI):
    """
    Custom ChatOpenAI wrapper for DeepSeek API compatibility.
    Handles the case where DeepSeek returns tool_calls.args as JSON strings instead of dicts.
    """

    def _create_message_dicts(self, messages: list, stop: Optional[list] = None) -> list:
        """Override to handle response parsing. Safely delegate to parent if available."""
        parent_func = getattr(ChatOpenAI, "_create_message_dicts", None)
        if parent_func is not None:
            try:
                result = ChatOpenAI._create_message_dicts(self, messages, stop)  # type: ignore[attr-defined]
                return list(result) if result is not None else []
            except Exception:
                pass
        # Fallback normalization
        message_dicts = []
        for msg in messages:
            if isinstance(msg, dict):
                message_dicts.append(msg)
            else:
                role = getattr(msg, "role", None) or getattr(msg, "type", None) or "assistant"
                content = getattr(msg, "content", None) or ""
                message_dicts.append({"role": role, "content": content})
        return message_dicts
    def _generate(self, messages: list, stop: Optional[list] = None, run_manager=None, **kwargs):
        """Override generation to fix tool_calls format in responses"""
        result = super()._generate(messages, stop, run_manager, **kwargs)
        self._fix_tool_calls(result)
        return result
    async def _agenerate(self, messages: list, stop: Optional[list] = None, run_manager=None, **kwargs):
        """Override async generation to fix tool_calls format in responses"""
        result = await super()._agenerate(messages, stop, run_manager, **kwargs)
        self._fix_tool_calls(result)
        return result
    def _fix_tool_calls(self, result):
        """Helper to fix tool_calls format in generated messages"""
        for generation in result.generations:
            for gen in generation:
                msg = getattr(gen, "message", None)
                if msg is None: continue
                additional_kwargs = getattr(msg, "additional_kwargs", {})
                tool_calls = additional_kwargs.get("tool_calls")
                if not tool_calls: continue
                for tool_call in tool_calls:
                    func = tool_call.get("function")
                    if isinstance(func, dict) and isinstance(func.get("arguments"), str):
                        try:
                            func["arguments"] = json.loads(func["arguments"])
                        except json.JSONDecodeError:
                            pass
