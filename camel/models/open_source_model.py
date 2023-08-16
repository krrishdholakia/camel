# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
from types import GeneratorType
from typing import Any, Dict, List

from camel.messages import OpenAIMessage
from camel.models import BaseModelBackend
from camel.typing import ModelType
from camel.utils import BaseTokenCounter, OpenSourceTokenCounter


class OpenSourceModel(BaseModelBackend):
    r"""Class for interace with OpenAI-API-compatible servers running
    open-source models.
    """

    def __init__(
        self,
        model_type: ModelType,
        model_config_dict: Dict[str, Any],
    ) -> None:
        r"""Constructor for model backends of Open-source models.

        Args:
            model_type (ModelType): Model for which a backend is created,
                one of GPT_* series.
            model_config_dict (Dict[str, Any]): A dictionary that will
                be fed into openai.ChatCompletion.create().
        """
        super().__init__(model_type, model_config_dict)

        # Check whether the input model type is open-source
        if not model_type.is_open_source:
            raise ValueError(
                f"Model `{model_type}` is not a supported open-source model")

        # Check whether input model path is empty
        model_path: str | None = self.model_config_dict.get("model_path", None)
        if not model_path:
            raise ValueError("Path to open-source model is not provided.")
        self.model_path: str = model_path

        # Check whether the model name matches the model type
        self.model_name: str = self.model_path.split('/')[-1]
        if not self.model_type.validate_model_name(self.model_name):
            raise ValueError(
                f"Model name `{self.model_name}` does not match model type "
                f"`{self.model_type.value}`.")

        # Load the server URL and check whether it is None
        server_url: str | None = self.model_config_dict.get("server_url", None)
        if not server_url:
            raise ValueError(
                "URL to server running open-source LLM is not provided.")
        self.server_url: str = server_url

        # Reassemble the argument dictionary to be passed to the API
        self.model_config_dict = {
            key: value
            for key, value in self.model_config_dict.items()
            if key != "model_path" and key != "server_url"
        }

    def initialize_token_counter(self) -> BaseTokenCounter:
        r"""Initialize the token counter for open-source model backends.

        Returns:
            BaseTokenCounter: The token counter following the provided
                open-source model's tokenization style.
        """
        return OpenSourceTokenCounter(self.model_type, self.model_path)

    def run(
        self,
        messages: List[Dict],
    ) -> Dict[str, Any]:
        r"""Run inference of OpenAI chat completion.

        Args:
            messages (List[Dict]): Message list with the chat history
                in OpenAI API format.

        Returns:
            Dict[str, Any]: Response in the OpenAI API format.
        """
        import openai
        openai.api_base = self.server_url

        messages_openai: List[OpenAIMessage] = messages
        response = openai.ChatCompletion.create(messages=messages_openai,
                                                model=self.model_name,
                                                **self.model_config_dict)
        if not self.stream:
            if not isinstance(response, Dict):
                raise RuntimeError("Unexpected batch return from OpenAI API")
        else:
            if not isinstance(response, GeneratorType):
                raise RuntimeError("Unexpected stream return from OpenAI API")
        return response

    @property
    def stream(self) -> bool:
        r"""Returns whether the model is in stream mode,
            which sends partial results each time.
        Returns:
            bool: Whether the model is in stream mode.
        """
        return self.model_config_dict.get('stream', False)
