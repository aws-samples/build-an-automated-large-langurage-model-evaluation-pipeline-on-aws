
def handler(event, context):
    execution_id = event['executionId'].split(":")[-1]
    payload = event['input']
    # Fetch the multiline string from the incoming event data
    multiline_string = payload.get('prompts', '').get("prompts", '').strip()
    model_name = payload.get("model_name")
    model_family = payload.get("model_family")
    method = payload.get("method", "native")

    # Split the string into an array using newline as the delimiter
    split_string_array = multiline_string.split('\n')

    array = [{"execution_id": execution_id, "model_family": model_family, "model_name": model_name, "prompt": prompt, "method": method}
             for prompt in split_string_array if prompt != "id|QUESTION|CONTEXT|Expected Answer"]

    # Return the array in the response
    return {
        "result": array
    }