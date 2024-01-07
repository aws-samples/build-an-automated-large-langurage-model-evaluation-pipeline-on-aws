
def handler(event, context):
    execution_id = event['executionId'].split(":")[-1]
    payload = event['input']
    # Fetch the multiline string from the incoming event data
    multiline_string = payload.get('prompts', '').get("prompts", '').strip()
    invoke_model_name = payload.get("invoke_model_name")
    invoke_model_family = payload.get("invoke_model_family")

    # Split the string into an array using newline as the delimiter
    split_string_array = multiline_string.split('\n')

    array = [{"execution_id": execution_id, "invoke_model_family": invoke_model_family, "invoke_model_name": invoke_model_name, "prompt": prompt}
             for prompt in split_string_array if prompt != "id|QUESTION|CONTEXT|Expected Answer"]

    # Return the array in the response
    return {
        "result": array
    }