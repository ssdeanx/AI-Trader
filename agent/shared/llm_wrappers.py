import json
from typing import Optional, Dict, Any, List, Union, cast
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel

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

class ChatModelFactory:
    """
    Factory class to create and configure LangChain chat models.
    Supports OpenAI, OpenRouter, DeepSeek, and Google Gemini.
    """

    @staticmethod
    def create_model(
        provider: str,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_retries: int = 3,
        timeout: int = 30,
        streaming: bool = False,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Union[BaseChatModel, Any]:
        """
        Create a chat model based on provider and configurations.
        """
        extra_params = extra_params or {}
        
        if provider == "google":
            # Gemini-specific settings
            settings = {
                "model": model_name,
                "google_api_key": api_key,
                "temperature": temperature,
                "max_retries": max_retries,
                "timeout": timeout,
                "streaming": streaming,
                "convert_system_message_to_human": extra_params.get("convert_system_message_to_human", False),
            }
            
            # Add safety settings if provided
            if "safety_settings" in extra_params:
                settings["safety_settings"] = extra_params["safety_settings"]
                
            # Add transport if provided
            if "transport" in extra_params:
                settings["transport"] = extra_params["transport"]

            model = ChatGoogleGenerativeAI(**settings)
            
            # Handle Search Grounding (if supported in langchain-google-genai)
            if extra_params.get("google_search_grounding", False):
                # Using tool grounding pattern for latest version
                model = model.bind(tools=[{"google_search_retrieval": {}}])
                
            return model

        elif provider in ["openai", "openrouter"]:
            settings = {
                "model": model_name,
                "api_key": api_key,
                "temperature": temperature,
                "max_retries": max_retries,
                "timeout": timeout,
                "streaming": streaming,
            }
            
            if base_url:
                settings["base_url"] = base_url
            elif provider == "openrouter":
                settings["base_url"] = "https://openrouter.ai/api/v1"

            # Use DeepSeek wrapper for DeepSeek models
            if "deepseek" in model_name.lower():
                return DeepSeekChatOpenAI(**settings)
            
            return ChatOpenAI(**settings)

        else:
            raise ValueError(f"Unsupported provider: {provider}")
