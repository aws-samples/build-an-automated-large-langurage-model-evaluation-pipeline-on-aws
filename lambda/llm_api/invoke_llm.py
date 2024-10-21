# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Shows how to use the Converse API with Anthropic Claude 3 Sonnet (on demand).
"""

import logging
import boto3

from botocore.exceptions import ClientError

bedrock_client = boto3.client(service_name='bedrock-runtime')
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def generate_result(bedrock_client,
                      model_id,
                      system_prompts,
                      messages, **kwargs):
    """
    Sends messages to a model.
    Args:
        bedrock_client: The Boto3 Bedrock runtime client.
        model_id (str): The model ID to use.
        system_prompts (JSON) : The system prompts for the model to use.
        messages (JSON) : The messages to send to the model.

    Returns:
        response (JSON): The conversation that the model generated.

    """

    logger.info("Generating message with model %s", model_id)

    # Inference parameters to use.
    temperature = kwargs.get("temperature", 0.5)
    top_k = kwargs.get("top_k", 250)
    top_p = kwargs.get("top_p", 1.0)
    max_tokens = kwargs.get("max_tokens", 200)

    # Base inference parameters to use.
    inference_config = {"temperature": temperature, "topK": top_k, "topP": top_p, "maxTokens": max_tokens}
    # Additional inference parameters to use.
    additional_model_fields = {"top_k": top_k}

    # Send the message.
    if system_prompts:
        response = bedrock_client.converse(
            modelId=model_id,
            messages=messages,
            system=system_prompts,
            inferenceConfig=inference_config,
            additionalModelRequestFields=additional_model_fields
        )
    else:
        response = bedrock_client.converse(
            modelId=model_id,
            messages=messages,
            inferenceConfig=inference_config,
            additionalModelRequestFields=additional_model_fields
        )
    # Log token usage.
    logger.info(response['output']['message'])
    text_result = response['output']['message']['content'][0]['text']
    logger.info("Generated text: %s", text_result)
    return text_result